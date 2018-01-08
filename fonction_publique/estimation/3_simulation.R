################ Simulation with multinomial logit ################


# Simulation of trajectories based on estimation of the model. 
# Two types of simulations: 
#     i) Simulation of grade exit (2011 --> 2015) 
#     ii)  Simulation of next ib (2011 --> 2012)

# Program: 
# 0.  Initialisation: data loading and variable creations
# I.  Estimation: estimation of the models for predictions
# II. Simulation: from estimates, creating the two outputs for simulation diagnosis. 



#### 0. Initialisation ####

source(paste0(wd, "0_Outils_CNRACL.R")) 
load(paste0(save_model_path, "mlog.rda"))
load(paste0(save_model_path, "m1_seq.rda"))
load(paste0(save_model_path, "m2_seq.rda"))
load(paste0(save_model_path, "m1_by_grade.rda"))

set.seed(1234)


generate_data_sim <- function(data_path, use = "min")
{
datasets = load_and_clean(data_path, dataname = "filter/data_ATT_2011_filtered_after_duration_final.csv")
if (use == "max"){data = datasets[[1]]}
if (use == "min"){data = datasets[[2]]}
list_var = c("ident", "annee",  "sexe", "c_cir_2011", "generation", "an_aff", "grade", 
             "E_exam", "E_choice", "D_exam", "D_choice",
             "time", "anciennete_dans_echelon", "echelon", "ib")
data = data[which(data$left_censored == F  & data$annee == 2011 & data$generation < 1990),
                    list_var ]
data_sim  =  create_variables(data) 
data_sim = data_sim[order(data_sim$ident), ]
return(data_sim)
}

generate_data_output <- function(data_path)
{
  dataname = "filter/data_ATT_2011_filtered_after_duration_final.csv"
  filename = paste0(data_path, dataname)
  data_long = read.csv(filename)
  data_long$grade = data_long$c_cir
  data_long$situation = data_long$next_grade_situation
  list_var = c("ident", "annee", "c_cir_2011", "sexe", "generation", "grade","ib", "echelon", "situation", "annee_entry_min", "annee_entry_max", "an_aff")
  output = data_long[which(data_long$annee >= 2011 & data_long$annee <= 2015), list_var]
  output$I_bothC = NULL
  return(output[, list_var])
}


save_prediction_R <- function(data, annee, save_path, modelname)
{
  data$corps = "ATT"
  data$next_situation = data$yhat
  data = data[, c("ident", "annee", "corps", "grade", "ib", "echelon", "anciennete_dans_echelon", "next_situation")]
  filename = paste0(save_path, annee, "_data_simul_withR_",modelname,".csv")
  write.csv(data, file = filename)
  print(paste0("Data ", filename, " saved"))
}


launch_prediction_Py <- function(annee, modelname, debug = F)
{
input_name = paste0(annee, "_data_simul_withR_",modelname,".csv")
output_name = paste0(annee, "_data_simul_withPy_",modelname,".csv")
input_arg = paste0(" -i ", input_name)
output_arg = paste0(" -o ", output_name)
d = ifelse(debug, " -d", "")
args = paste0(input_arg, output_arg, d)
command =  paste0('simulation',  args)
shell(command)
}


load_simul_py <- function(annee, modelname)
{
  filename = paste0(simul_path, paste0(annee, "_data_simul_withPy_",modelname,".csv"))
  simul = read.csv(filename)  
  simul = simul[order(simul$ident),-1]
  #names(simul) = c("ident", "next_annee", "next_grade", "next_echelon", "next_annicennete_dans_echelon")
  return(simul)
}


# Prédiction du changement de grade pour le modèle multinomial simple
predict_next_year_MNL <- function(data_sim, model, modelname)
{
  adhoc <- sample(c("no_exit",   "exit_next", "exit_oth"), nrow(data_sim), replace=TRUE, prob = c(0.2, 0.2, 0.6))
  data_sim$next_year <-adhoc
  data_sim$grade <-as.character(data_sim$grade)
  # Prediction for AT grade
  data_AT = data_sim[which(is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
  data_predict_MNL <- mlogit.data(data_AT, shape = "wide", choice = "next_year") 
  data_predict_MNL = data_predict_MNL[order(data_predict_MNL$ident, data_predict_MNL$alt),]
  prob     <- predict(model, data_predict_MNL ,type = "response") 
  data_AT$yhat <- mapply(tirage_next_year_MNL, prob[,1], prob[,2], prob[,3])
  
  # Correct 1: individuals in TTH4 cannot go in 'exit_next'
  to_change = which(data_AT$grade == "TTH4" & data_AT$yhat == "exit_next")
  rescale_p_no_exit = prob[,1]/(prob[,1]+prob[,3])
  no_exit_hat   <- as.numeric(mapply(tirage, rescale_p_no_exit))
  data_AT$yhat[to_change] <- ifelse(no_exit_hat[to_change]  == 1, "no_exit", "exit_oth")

  # Correct 2: individuals in TTM1 or TTM2 stay in their grade.
  if (length(unique(data_sim$grade)) > 4)
  {
    data_noAT = data_sim[which(!is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
    data_noAT$yhat = "no_exit" 
    data_sim = rbind(data_AT, data_noAT)  
  }
  if (length(unique(data_sim$grade)) <= 4)
  {
    data_sim = data_AT
  }
  data_sim = data_sim[order(data_sim$ident), ]
  return(data_sim)
}



# Prédiction du changement de grade pour le modèle par grade
predict_next_year_byG <- function(data_sim, list_model, modelname)
{
  adhoc <- sample(c("no_exit",   "exit_next", "exit_oth"), nrow(data_sim), replace=TRUE, prob = c(0.2, 0.2, 0.6))
  data_sim$next_year <-adhoc
  data_sim$grade <- as.character(data_sim$grade)
  data_sim$yhat = ""
  data_predict = mlogit.data(data_sim, shape = "wide", choice = "next_year")  
  data_predict = data_predict[order(data_predict$ident, data_predict$alt),]
  # Prediction by grade
  n = names(data_sim)
  data_merge = as.data.frame(setNames(replicate(length(n),numeric(0), simplify = F), n))
  list_grade = c("TTH1","TTH2", "TTH3", "TTH4")
  for (g in 1:length(list_grade))
  {
    list_id_sim   = which(data_sim$grade == list_grade[g])
    list_id_estim = which(data_predict$grade == list_grade[g])
    model = list_model[[g]]
    if (list_grade[g] != "TTH4")
    {
    prob     <- predict(model, data_predict[list_id_estim, ], type = "response") 
    data_sim$yhat[list_id_sim] = mapply(tirage_next_year_MNL, prob[,1], prob[,2], prob[,3])
    }
    if (list_grade[g] == "TTH4")
    {
    prob     <- predict(model, data_sim[list_id_sim, ] ,type = "response") 
    pred     <- as.numeric(mapply(tirage, prob))
    data_sim$yhat[list_id_sim] = ifelse(pred == 1, "exit_oth", "no_exit")
    }

  }

  # No exit quand hors du corps
  if (length(unique(data_sim$grade)) > 4)
  {
    list_hors_corps = which(!is.element(data_sim$grade, list_grade))
    data_sim$yhat[list_hors_corps] = "no_exit" 
  }
  data_sim = data_sim[order(data_sim$ident), ]
  
  # Checks
  stopifnot(length(which(data_sim$yhat == "")) == 0)
  return(data_sim)
}


predict_next_year_seq_m1 <- function(data_sim, m1, m2, modelname)
{
  # Prediction for AT grade
  data_AT = data_sim[which(is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
  prob1     <- predict(m1, data_AT, type = "response")  
  pred1     <- as.numeric(mapply(tirage, prob1))
  prob2     <- predict(m2, data_AT, type = "response")  
  pred2     <- as.numeric(mapply(tirage, prob2))
  data_AT$yhat <- ifelse(pred1 == 1, "exit", "no_exit")
  data_AT$yhat[which(pred1 == 1 & pred2 == 1)] <- "exit_next"
  data_AT$yhat[which(pred1 == 1 & pred2 == 0)] <- "exit_oth"
  
  # Correct: exit_next to oth when TTH4.
  data_AT$yhat[which(data_AT$grade == "TTH4" & data_AT$yhat == "exit_next")] <- "exit_oth"
  
  if (length(unique(data_sim$grade)) > 4)
  {
    data_noAT = data_sim[which(!is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
    data_noAT$yhat = "no_exit" 
    data_sim = rbind(data_AT, data_noAT)  
  }
  if (length(unique(data_sim$grade)) <= 4)
  {
    data_sim = data_AT
  }
  data_sim = data_sim[order(data_sim$ident), ]
  return(data_sim)
}

predict_next_year_seq_m2 <- function(data_sim, m1, m2, modelname)
{
  # Prediction for AT grade
  data_AT = data_sim[which(is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
  prob1     <- predict(m1, data_AT, type = "response")  
  pred1     <- as.numeric(mapply(tirage, prob1))
  prob2     <- predict(m2, data_AT, type = "response")  
  pred2     <- as.numeric(mapply(tirage, prob2))
  data_AT$yhat <- ifelse(pred1 == 1, "exit_oth", "no_exit")
  data_AT$yhat[which(pred1 == 0 & pred2 == 1)] <- "exit_next"
  data_AT$yhat[which(pred1 == 0 & pred2 == 0)] <- "no_exit"
  # Correct: exit_next to no_exit when TTH4.
  data_AT$yhat[which(data_AT$grade == "TTH4" & data_AT$yhat == "exit_next")] <- "no_exit"
  
  if (length(unique(data_sim$grade)) > 4)
  {
    data_noAT = data_sim[which(!is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
    data_noAT$yhat = "no_exit" 
    data_sim = rbind(data_AT, data_noAT)  
  }
  if (length(unique(data_sim$grade)) <= 4)
  {
    data_sim = data_AT
  }
  data_sim = data_sim[order(data_sim$ident), ]
  return(data_sim)
}


increment_data_sim <- function(data_sim, simul_py)
{
  # Deleting individuals with pbl
  if (length(data_sim$ident) != length(simul_py$ident) | length(which(is.na(simul_py$ib)) >0 )  | 
      length(which(is.na(simul_py$grade)) >0 | length(which(!is.element(simul_py$echelon, seq(1,12))))>0 ))
  {
    
    list_pbl_id1 = unique(setdiff(data_sim$ident, simul_py$ident))
    print(paste0("Il y a ",length(list_pbl_id1)," présents dans data_sim et absent dans simul"))
    
    list_pbl_id2 = unique(setdiff(simul_py$ident, data_sim$ident))
    print(paste0("Il y a ",length(list_pbl_id2)," présents dans simul et absent dans data_sim"))
    
    list_pbl_ib = unique(simul_py$ident[which(is.na(simul_py$ib))])
    print(paste0("Il y a ",length(list_pbl_ib)," individus dans la base simul  avec ib = NA"))
    
    list_pbl_grade = unique(simul_py$ident[which(is.na(simul_py$grade) | simul_py$grade == "nan")])
    print(paste0("Il y a ",length(list_pbl_grade)," individus dans la simul  avec grade = NA"))
    
    list_pbl_echelon = unique(simul_py$ident[which(!is.element(simul_py$echelon, seq(1,12)))])
    print(paste0("Il y a ",length(list_pbl_grade)," individus dans la simul  avec echelon bizarre"))
    
    
    deleted_id = Reduce(union, list(list_pbl_id1, list_pbl_id2, list_pbl_ib, list_pbl_grade, list_pbl_echelon))
    
    stopifnot(length(deleted_id) == 0)
    
    data_sim = data_sim[which(!is.element(data_sim$ident, deleted_id)), ]
    simul_py = simul_py[which(!is.element(simul_py$ident, deleted_id)), ]
    
    print(paste0("Il y a ",length(unique(data_sim$ident))," individus dans la base en ", annee+1))
  }
  # Merge
  list_var_kept1 = c("ident",  "sexe", "generation", "an_aff", "c_cir_2011",
               "E_exam", "E_choice", "D_exam", "D_choice", "time")
  list_var_kept2 = c("annee", "grade", "echelon", "ib", "anciennete_dans_echelon", "situation")
  data_merge = cbind(data_sim[,list_var_kept1], simul_py[, list_var_kept2])
  
  # Increment time
  data_merge$time[which(data_merge$situation == "no_exit")] = data_merge$time[which(data_merge$situation == "no_exit")] + 1
  data_merge$time[which(data_merge$situation != "no_exit")] = 1
  
  # Recreate variables (duration, thresholds with new time and echelons)
  data_merge  =  create_variables(data_merge) 
  data_merge = data_merge[order(data_merge$ident), ]
  return(data_merge)
}


save_results_simul <- function(output, data_sim, modelname)
{
  var = c("grade", "anciennete_dans_echelon", "echelon", "ib", "situation", "I_bothC")
  new_var = paste0(c("grade", "anciennete_dans_echelon", "echelon", "ib", "situation", "I_bothC"), "_", modelname )
  data_sim[, new_var] = data_sim[, var]
  add = data_sim[, c("ident", "annee", new_var)]
  # Merge
  output = rbind(output, add)
  output = output[order(output$ident, output$annee),]
  return(output)
}


########## II. Simulation #########

output_global = generate_data_output(data_path)

add = generate_data_output(data_path)

for (m in 1:6)
{
  if (m <= 3){modelname  =  paste0("MNL_", toString(m))}  
  if (m == 4){modelname = "BG_1"}
  if (m == 5){modelname = "MS_1"}
  if (m == 6){modelname = "MS_2"}
  print(paste0("Simulation for model ", modelname))
  for (annee in 2011:2014)
  { 
    print(paste0("Annee ", annee))
    if (annee == 2011)
    {
      data_sim = generate_data_sim(data_path, use = "min")
      output = data_sim[, c("ident", "annee", "grade","ib", "anciennete_dans_echelon", "echelon", "I_bothC")]
      output = rename(output, c("grade"=paste0("grade_", modelname) , 
                                "ib"=paste0("ib_", modelname), 
                                "anciennete_dans_echelon"=paste0("anciennete_dans_echelon_", modelname),
                                "echelon"=paste0("echelon_", modelname),
                                "I_bothC"=paste0("I_bothC_", modelname)))
      output[, paste0("situation_", modelname)] = NA
    }
    # Prediction of next_situation from estimated model 
    if (m <= 3){pred =  predict_next_year_MNL(data_sim, model = list_MNL[[m]], modelname)} 
    if (m == 4){pred =  predict_next_year_byG(data_sim, list_by_grade, modelname)}
    if (m == 5){pred =  predict_next_year_seq_m1(data_sim, step1_m1, step2_m1, modelname)}
    if (m == 6){pred =  predict_next_year_seq_m2(data_sim, step1_m2, step2_m2, modelname)}
    stopifnot(length(which(pred$yhat == "exit_next" & pred$grade == "TTH4")) == 0)
    # Save prediction for Py simulation
    output[which(output$annee == annee), paste0("situation_", modelname)] = pred$yhat
    
    # Check 
    list_id1 = output$ident[which(output$annee == annee & output$situation_BG_1 == "exit_next")]
    list_id2 = pred$ident[which(pred$yhat == "exit_next")]
    stopifnot(length(setdiff(list_id1, list_id2))==0)
    
    save_prediction_R(data = pred, annee, simul_path, modelname)
    # Prediction of next_ib using simulation.py
    launch_prediction_Py(annee, modelname)
    # Load 
    simul_py = load_simul_py(annee, modelname)
    # Incrementing data_sim for next year
    data_sim = increment_data_sim(data_sim, simul_py)
    
    # Save results
    output = save_results_simul(output, data_sim, modelname)
  }
  output_global = merge(output_global, output, by = c("ident", "annee"), all.x = T)
}

save(output_global, file = paste0(simul_path, "predictions10.Rdata"))


