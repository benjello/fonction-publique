


## I. Packages
list_packages = list()
if (!require("pacman")) install.packages("pacman")
pacman::p_load(OIsurv, rms, emuR, RColorBrewer, flexsurv, mfx, devtools, plyr, lazyeval, ggplot2, gridExtra, grid, hydroGOF,
               texreg, xtable, mlogit, data.table, pscl)


## I. Managing data #####

load_and_clean = function(data_path, dataname)
# Input: inital data (name and path)
# Ouput: two datasets, with two definitions of duration in grade
{
  ## Chargement de la base
  filename = paste0(data_path, dataname)
  data_long = read.csv(filename)

  ## Variables creation ####

  # Format bolean                     
  to_bolean = c("change_grade", "right_censored")
  data_long[, to_bolean] <- sapply(data_long[, to_bolean], as.logical)
  
  data_long$observed  = ifelse(data_long$right_censored == 1, 0, 1) 
  data_long$echelon_2011 = ave(data_long$echelon*(data_long$annee == 2011), data_long$ident, FUN = max)
  data_long$last_y_in_grade = data_long$annee_exit - 1
  
  data_long$grade = as.character(data_long$c_cir)
  
  # Duration variables
  data_long$time_spent_in_grade_max  = data_long$annee - data_long$annee_entry_min + 1
  data_long$time_spent_in_grade_min  = data_long$annee - data_long$annee_entry_max + 1
  data_long$anciennete_dans_echelon  = data_long$anciennete_echelon
  # Exit_status
  data_long$exit_status2 = ifelse(data_long$annee == data_long$last_y_in_grade, 1, 0)
  data_long$exit_status2[data_long$right_censored] = 0

  data_long$next_year = as.character(data_long$next_grade_situation)

  data_long = data_long[order(data_long$ident,data_long$annee),]
  
  ## Institutional parameters (question: default value?)
  # Grade duration
  data_long$D_exam = 20
  data_long$D_exam[which(data_long$c_cir_2011 == "TTH1")] = 3
  data_long$D_choice = 20
  data_long$D_choice[which(data_long$c_cir_2011 == "TTH1")] = 10
  data_long$D_choice[which(data_long$c_cir_2011 == "TTH2")] = 6
  data_long$D_choice[which(data_long$c_cir_2011 == "TTH3")] = 5
  
  # Echelon (default = ?)
  data_long$E_exam = 12
  data_long$E_exam[which(data_long$c_cir_2011 == "TTH1")] = 4
  data_long$E_choice = 12
  data_long$E_choice[which(data_long$c_cir_2011 == "TTH1")] = 7
  data_long$E_choice[which(data_long$c_cir_2011 == "TTH2")] = 5
  data_long$E_choice[which(data_long$c_cir_2011 == "TTH3")] = 6
  
  # Next ib
  data_long$next_ib <-ave(data_long$ib, data_long$ident, FUN=shift1)
  data_long$var_ib  <-(data_long$next_ib - data_long$ib)/data_long$ib
  
  ## Data for estimations ####
  data_long = data_long[which(data_long$annee <= data_long$last_y_in_grade),]
  
  # One line per year of observation (min and max)
  data_min = data_long[which(data_long$annee >= data_long$annee_entry_min),]
  data_min$time = data_min$time_spent_in_grade_max 
  data_max = data_long[which(data_long$annee >= data_long$annee_entry_max),]
  data_max$time = data_max$time_spent_in_grade_min
  
  # Modif: time = an_aff when TTH1
  data_max$dist_an_aff = data_max$annee - data_max$an_aff +1 
  data_max$time[which(data_max$grade == "TTH1")] = data_max$dist_an_aff[which(data_max$grade == "TTH1")]
  data_min$dist_an_aff = data_min$annee - data_min$an_aff
  data_min$time[which(data_min$grade == "TTH1")] = data_min$dist_an_aff[which(data_min$grade == "TTH1")]
  
  # One line per ident data
  data_id = data_long[!duplicated(data_long$ident),]
  
  # Tests
  stopifnot(length(unique(data_id$ident)) == length(unique(data_max$ident)) | length(unique(data_id$ident)) == length(unique(data_min$ident)))
  
  return(list(data_max, data_min))
}  


# Variable creations 
create_variables <- function(data)
{
  # Generation group
  data$generation_group  <-cut(data$generation, c(1960,1965,1970,1975,1980,1985,1990), labels=c(1:6))
  data$generation_group2 <-cut(data$generation, c(1960,1969,1979,1989), labels = c(1:3))

  data$c_cir_2011 = factor(data$c_cir_2011)
  
  data$age_an_aff    = data$an_aff - data$generation
  data$dist_an_aff = data$annee - data$an_aff +1 
  grade_modif = which(data$grade == "TTH1" | data$grade == "TTH2")
  data$time2 = data$time
  data$time2[grade_modif] = data$dist_an_aff[grade_modif] 
  data$I_echC     = ifelse(data$echelon >= data$E_choice, 1, 0) 
  data$I_gradeC   = ifelse(data$time2 >= data$D_choice, 1, 0) 
  data$I_bothC    =  ifelse(data$I_echC ==1 &  data$I_gradeC == 1, 1, 0) 
  data$I_echE     = ifelse(data$echelon >= data$E_exam & data$grade == "TTH1", 1, 0) 
  data$I_gradeE   = ifelse(data$time2 >= data$D_exam & data$grade == "TTH1", 1, 0) 
  data$I_bothE    = ifelse(data$I_echE ==1 &  data$I_gradeE == 1, 1, 0) 

  data$cum_bothC = ave(data$I_bothC, data$ident, FUN = cumsum)
  data$I_bothC_bis = ifelse(data$cum_bothC >= 1 & data$cum_bothC <=3, 1, 0) 
  
  data$cum_bothE = ave(data$I_bothE, data$ident, FUN =  cumsum)
  data$I_bothE_bis = ifelse(data$cum_bothE >= 1 & data$cum_bothE <=3, 1, 0) 
  

  grille_ech = data.frame(echelon =  seq(1, 11), duree_min= c(12, 24, 24, 36, 36, 36, 48, 48, 48, 48, 48))
  grille_ech$cum_duree = cumsum(grille_ech$duree_min)
  # Distance au seuil "au choix" (A AMELIORER)
  data = merge(data, grille_ech, by = "echelon", all.x = T) 
  data$refC = 999
  for (grade in c("TTH1", "TTH2", "TTH3"))
  {
  list = which(data$c_cir_2011 == grade)
  if (grade == "TTH1"){data$refC[list] = grille_ech$cum_duree[which(grille_ech$echelon == 7 )]}
  if (grade == "TTH2"){data$refC[list] = grille_ech$cum_duree[which(grille_ech$echelon == 5 )]}
  if (grade == "TTH3"){data$refC[list] = grille_ech$cum_duree[which(grille_ech$echelon == 6 )]}
  }
  data$dist_dureeC = data$cum_duree - data$refC
  data$a = 1
  data$duree_in_echC  = ave(data$a, list(data$ident, data$grade, data$echelon), FUN = cumsum)
  data$dist_ech_condC = (data$dist_dureeC)/12 + data$duree_in_echC
  
  data$dist_grade_condC = data$time2 - data$D_choice
  data$dist_threshold_bef = pmin(0, pmin(data$dist_grade_condC, data$dist_ech_condC ))
  data$dist_threshold_aft = pmax(0, pmin(data$dist_grade_condC, data$dist_ech_condC ))
  data$dist_thresholdC = data$dist_threshold_bef + data$dist_threshold_aft
  
  data$T_condC = ifelse(data$dist_thresholdC >= 0 & data$dist_thresholdC <= 1, 1, 0)
  data$I_condC = ifelse(data$dist_thresholdC >= 0, 1, 0)
  
    
  # Distance au seuil "exam" (A AMELIORER)
  data$refE = 999
  list = which(data$c_cir_2011 == "TTH1")
  data$refE[list] = grille_ech$cum_duree[which(grille_ech$echelon == 4 )]
  data$dist_dureeE = data$cum_duree - data$refE
  data$a = 1
  data$duree_in_echE  = ave(data$a, list(data$ident, data$grade, data$echelon), FUN = cumsum)
  data$dist_ech_condE = (data$dist_dureeE)/12 + data$duree_in_echE
  
  data$dist_grade_condE = data$time2 - data$D_exam
  data$dist_threshold_bef = pmin(0, pmin(data$dist_grade_condE, data$dist_ech_condE ))
  data$dist_threshold_aft = pmax(0, pmin(data$dist_grade_condE, data$dist_ech_condE ))
  data$dist_thresholdE = data$dist_threshold_bef + data$dist_threshold_aft
  
  data$T_condE = ifelse(data$dist_thresholdE >= 0 & data$dist_thresholdE <= 1, 1, 0)
  data$I_condE = ifelse(data$dist_thresholdE >= 0, 1, 0)
  
  
  ### Variables de durées
  data$duration  = data$time
  data$duration2 = data$time^2 
  data$duration3 = data$time^3 
  
  data$aft_seuil  = ifelse(data$I_condC == 1, data$duration, 0)
  data$aft_seuil2 = data$aft_seuil^2
  data$bef_seuil  = ifelse(data$I_condC == 0, data$duration, 0)
  data$bef_seuil2 = data$bef_seuil^2
  
  data$aft_seuil_TTH1  = ifelse(data$I_condC == 1, data$duration, 0)
  data$aft_seuil2_TTH1 = data$aft_seuil^2
  data$mid_seuil_TTH1  = ifelse(data$I_condC == 0 & data$I_condE == 1, data$duration, 0)
  data$mid_seuil2_TTH1 = data$mid_seuil^2
  data$bef_seuil_TTH1  = ifelse(data$I_condE == 0, data$duration, 0)
  data$bef_seuil2_TTH1 = data$bef_seuil^2
  
  return(data)
}


### II. Descriptive statistics

extract_exit = function(data, exit_var)
{
  data = data[, c("ident", "annee", "c_cir_2011", exit_var)]
  
  data$exit_var = data[, exit_var]
  data$ind_exit      = ifelse(data$exit_var != "no_exit", 1, 0) 
  data$ind_exit_cum  = ave(data$ind_exit, data$ident, FUN = cumsum)
  data$ind_exit_cum2  = ave(data$ind_exit_cum, data$ident, FUN = cumsum)
  data$ind_exit_cum2  = ave(data$ind_exit_cum, data$ident, FUN = cumsum)
  data$ind_exit_tot   = ave(data$ind_exit, data$ident, FUN = sum)
  ### PB  
  data$ind_first_exit  = ifelse(data$ind_exit_cum2 == 1, 1, 0) 
  data$ind_first_exit[which(is.na(data$ind_first_exit))] = 0
  data$year_exit = ave((data$ind_first_exit*data$annee), data$ident, FUN = max)
  data$year_exit[which(data$year_exit == 0)] = 2014
  data2 = data[which(data$annee == data$year_exit ),]
  data2$year_exit[which(data2$ind_exit_tot == 0)] = 9999
  stopifnot(length(unique(data2$ident)) == length(unique(data$ident)))
  data2 = data2[, c("ident", "c_cir_2011", "year_exit", "exit_var")]
  return(data2)
}  

compute_hazard= function(data, list, type_exit = "all")
{
  years = 2011:2014
  haz  = numeric(length(years))
  if (!is.element(type_exit, c("all", "exit_next", "exit_oth"))){print("wrong exit type"); return()}
  n = length(list)
  if (type_exit == "all")
  {
    for (y in 1:length(years)){
      haz[y] =  length(which(data$year_exit[list] == years[y]))/
        length(which(data$year_exit[list] >= years[y]))
    }
  }
  else{
    for (y in 1:length(years))
    {
      haz[y] =  length(which(data$year_exit[list] == years[y] & data$exit_var[list] == type_exit))/
        length(which(data$year_exit[list] >= (years[y])))
    }
  }
  return(haz)  
}

plot_hazards = function(hazard, colors, type, title)
{
  years = 2011:2014
  limits = c(0, max(hazard))
  plot(years,rep(NA,length(years)),ylim=limits, ylab="Hazard rate",xlab="Année")
  title(title)
  for (l in 1:nrow(hazard)){lines(years, hazard[l,], col =  colors[l], lwd = 3, lty = types[l])}  
}



# Hazard by duration in grade
hazard_by_duree = function(data, save = F, corps = F, type_exit = "")
{
  grade = seq(1, 12)
  hazard   = numeric(length(grade))
  effectif = numeric(length(grade))
  
  data$exit = data$exit_status2
  if (type_exit == "in_corps") {data$exit[which(data$next_year == "exit_oth")] = 0}
  if (type_exit == "out_corps"){data$exit[which(data$next_year == "exit_next")] = 0}
  
  for (g in 1:length(grade))
  {
    hazard[g]   = length(which(data$time ==  grade[g] & data$exit == 1))/length(which(data$time == grade[g]))
    effectif[g] = length(which(data$time == grade[g]))
  }  
  par(mar = c(5,5,2,5))
  xlabel = ifelse(corps, "Duration in section", "Duration in rank")
  plot(grade, hazard, type ="l", lwd = 3, xlab = xlabel, ylab = "Hazard rate", col = "darkcyan")
  par(new = T)
  plot(grade, effectif, type ="l", lty = 2, lwd = 2, axes=F, xlab=NA, ylab=NA)
  axis(side = 4)
  mtext(side = 4, line = 3, 'Nb obs.')
  legend("topleft", legend = c("Hazard", "Nb obs."), lwd = 3, lty = c(1,3), col = c("darkcyan", "black"), cex = 1.1)
}  

# Hazard by echelon
hazard_by_ech = function(data, save = F, type_exit = "")
{
  ech = 1:12
  hazard = numeric(length(ech))
  effectif = numeric(length(ech))
  
  data$exit = data$exit_status2
  if (type_exit == "in_corps") {data$exit[which(data$next_year == "exit_oth")] = 0}
  if (type_exit == "out_corps"){data$exit[which(data$next_year == "exit_next")] = 0}
  
  
  for (e in 1:length(ech))
  {
    hazard[e] =   length(which(data$echelon == ech[e] & data$exit == 1))/length(which(data$echelon == ech[e]))
    effectif[e] = length(which(data$echelon == ech[e]))
  }  
  
  par(mar = c(5,5,2,5))
  plot(ech, hazard, type ="l", lwd = 3, xlab = "Level", ylab = "Hazard rate", col = "darkcyan")
  par(new = T)
  plot(ech, effectif, type ="l", lty = 2, lwd = 2, axes=F, xlab=NA, ylab=NA)
  axis(side = 4)
  mtext(side = 4, line = 3, 'Nb. obs')
  legend("topleft", legend = c("Hazard", "Nb obs."), lwd = 3, lty = c(1,3), col = c("darkcyan", "black"), cex = 1.1)
}  



### III. Simulation tools ####
tirage_next_year_MNL <- function(p1,p2,p3)
{
  # random draw of next year situation based on predicted probabilities   
  n = sample(c("no_exit", "exit_next",  "exit_oth"), size = 1, prob = c(p1,p2,p3), replace = T)  
  return(n) 
}  



predict_next_grade <- function(next_situation, grade, exit_oth)
  # Predict next grade based on next situation and current situation.
  {
  # Default: same grade
  next_grade = as.character(grade)
  # Exit next: next
  next_grade[which(grade == "TTH1" & next_situation == "exit_next")] = "TTH2"
  next_grade[which(grade == "TTH2" & next_situation == "exit_next")] = "TTH3"
  next_grade[which(grade == "TTH3" & next_situation == "exit_next")] = "TTH4"
  # Exit oth: draw in probability
  for (g in c("TTH1", "TTH2", "TTH3", "TTH4"))
  {
  list1 = which(grade == g & next_situation == "exit_oth")
  data1 = data_exit_oth[which(data_exit_oth$c_cir == g),]
  table1 = table(data1$next_grade)/length(data1$next_grade)
  next_grade[list1]  = sample(names(table1), size = length(list1), prob = as.vector(table1), replace = T)  
  }
  return(next_grade) 
}  


extract_exit2 = function(data, exit_var, name)
# Fonction computing for each individual in data the year of exit and the grade of destination.
{
  data = data[, c("ident", "annee", exit_var)]
  data$exit_var = data[, exit_var]
  data$ind_exit       = ifelse(data$exit_var != "no_exit", 1, 0) 
  data$ind_exit_cum   = ave(data$ind_exit, data$ident, FUN = cumsum)
  data$ind_exit_cum2  = ave(data$ind_exit_cum, data$ident, FUN = cumsum)
  data$ind_exit_cum2  = ave(data$ind_exit_cum, data$ident, FUN = cumsum)
  data$ind_exit_tot   = ave(data$ind_exit, data$ident, FUN = sum)
  data$ind_first_exit  = ifelse(data$ind_exit_cum2 == 1, 1, 0) 
  data$year_exit = ave((data$ind_first_exit*data$annee), data$ident, FUN = max)
  data$year_exit[which(data$year_exit == 0)] = 2014
  data2 = data[which(data$annee == data$year_exit ),]
  data2$year_exit[which(data2$ind_exit_tot == 0)] = 9999
  data2 = data2[c("ident", "year_exit", "exit_var")]
  colnames(data2)= paste0(colnames(data2), "_", name)
  return(data2)
}  


### III. Graphes and tables 


plot_share = function(exit_data, plot = F, title = "")
{
  # Construction data  
  n_id = nrow(exit_data)
  exit_data =  exit_data[rep(seq_len(nrow(exit_data)), each=5),]  
  exit_data$annee = rep(seq(2011, 2015), n_id)
  exit_data$state = ifelse(exit_data$annee <= exit_data$year_exit, 3, 0)
  exit_data$state[which(exit_data$exit_var == "exit_next" & exit_data$state == 0)] = 2
  exit_data$state[which(exit_data$exit_var == "exit_oth"  & exit_data$state == 0)] = 1
  # Graphe shares
  df <- data.frame(Annee=numeric(),Status=numeric(),pct=numeric())
  date <- seq(2011, 2015)
  for (s in 1:3) 
  { 
    m <- matrix(ncol=3,nrow=length(date))
    m[,1] <- s
    m[,2] <- date
    for (a in 1:length(date))
    {
      m[a,3]<- length(which(exit_data$annee==date[a] & exit_data$state == s))/length(which(exit_data$annee==date[a]))
    }  
    df <- rbind(df,as.data.frame(m))
  }  
  names(df) <- c("status","date","pct")
  df$status2 <- as.factor(df$status)
  s_titles <-  c("Sortie hors corps", "Sortie dans corps", "Grade initial")
  n_col <- c("grey10", "grey40", "grey80")
  p1 = ggplot(df, aes(x=date, y=pct, fill=status2)) + geom_area()+
    scale_fill_manual(name="", values = n_col[1:6], labels=s_titles)+
    scale_y_continuous( expand = c(0, 0)) +  scale_x_continuous( expand = c(0, 0)) + 
    xlab("Annee")+ylab("Proportion")  + theme_bw() 
  if (title != ""){p1 = p1 + ggtitle(title)}
  if (plot){p1}
  return(p1)
}  


### IV. Generic functions #####


shift<-function(x,shift_by){
  stopifnot(is.numeric(shift_by))
  stopifnot(is.numeric(x))
  
  if (length(shift_by)>1)
    return(sapply(shift_by,shift, x=x))
  
  out<-NULL
  abs_shift_by=abs(shift_by)
  if (shift_by > 0 )
    out<-c(tail(x,-abs_shift_by),rep(NA,abs_shift_by))
  else if (shift_by < 0 )
    out<-c(rep(NA,abs_shift_by), head(x,-abs_shift_by))
  else
    out<-x
  out
}


shiftm1<- function(x)  #adapt? de shift  : cr?er une variable d?cal?e de 1 vers le base. 
{
  out <- shift(x,-1)
  return(out)
}


shift1<-function(x){
  stopifnot(is.numeric(x))
  out<-NULL
  abs_shift_by=1
  out<-c(tail(x,-abs_shift_by),rep(NA,abs_shift_by))
  out
}

tirage<-function(var)
{
  t<-rbinom(1,1,var) # Loi binomiale 
  return(t)
}


build.ror <- function(final.rnames, name.map,add.omit=NULL){
  keep <- final.rnames %in% names(name.map)
  mapper <- function(x){
    mp <- name.map[[x]] 
    ifelse(is.null(mp), x, mp)
  }
  newnames <- sapply(final.rnames, mapper)
  omit <- paste0(paste0(final.rnames[!keep], collapse="|"),add.omit)
  reorder <- na.omit(match(unlist(name.map), newnames[keep]))
  
  list(ccn=newnames, oc=omit, rc=reorder)
}

all.varnames.dammit <- function(model.list){
  mods <- texreg:::get.data(model.list)
  gofers <- texreg:::get.gof(mods)
  mm <- texreg:::aggregate.matrix(mods, gofers, digits=3)
  rownames(mm)
}


mfx <- function(x,sims=1000){
  set.seed(1984)
  pdf <- ifelse(as.character(x$call)[3]=="binomial(link = \"probit\")",
                mean(dnorm(predict(x, type = "link"))),
                mean(dlogis(predict(x, type = "link"))))
  pdfsd <- ifelse(as.character(x$call)[3]=="binomial(link = \"probit\")",
                  sd(dnorm(predict(x, type = "link"))),
                  sd(dlogis(predict(x, type = "link"))))
  marginal.effects <- pdf*coef(x)
  sim <- matrix(rep(NA,sims*length(coef(x))), nrow=sims)
  for(i in 1:length(coef(x))){
    sim[,i] <- rnorm(sims,coef(x)[i],diag(vcov(x)^0.5)[i])
  }
  pdfsim <- rnorm(sims,pdf,pdfsd)
  sim.se <- pdfsim*sim
  res <- cbind(marginal.effects,sd(sim.se))
  colnames(res)[2] <- "standard.error"
  ifelse(names(x$coefficients[1])=="(Intercept)",
         return(res[2:nrow(res),]),return(res))
}


mfx2<- function(modform,dist,data,boot=1000,digits=3){
  x <- glm(modform, family=binomial(link=dist),data)
  # get marginal effects
  pdf <- ifelse(dist=="probit",
                mean(dnorm(predict(x, type = "link"))),
                mean(dlogis(predict(x, type = "link"))))
  marginal.effects <- pdf*coef(x)
  # start bootstrap
  bootvals <- matrix(rep(NA,boot*length(coef(x))), nrow=boot)
  set.seed(1111)
  for(i in 1:boot){
    samp1 <- data[sample(1:dim(data)[1],replace=T,dim(data)[1]),]
    x1 <- glm(modform, family=binomial(link=dist),samp1)
    pdf1 <- ifelse(dist=="probit",
                   mean(dnorm(predict(x1, type = "link"))),
                   mean(dlogis(predict(x1, type = "link"))))
    bootvals[i,] <- pdf1*coef(x1)
  }
  res <- cbind(marginal.effects,apply(bootvals,2,sd),marginal.effects/apply(bootvals,2,sd))
  if(names(x$coefficients[1])=="(Intercept)"){
    res1 <- res[2:nrow(res),]
    res2 <- matrix(as.numeric(sprintf(paste("%.",paste(digits,"f",sep=""),sep=""),res1)),nrow=dim(res1)[1])     
    rownames(res2) <- rownames(res1)
  } else {
    res2 <- matrix(as.numeric(sprintf(paste("%.",paste(digits,"f",sep=""),sep="")),nrow=dim(res)[1]))
    rownames(res2) <- rownames(res)
  }
  colnames(res2) <- c("marginal.effect","standard.error","z.ratio")  
  return(res2)
}


extract.glm2<-function (model, include.aic = F, include.bic = F, include.loglik = TRUE, 
                        include.deviance = F, include.nobs = TRUE,include.pseudoR2 = TRUE) 
{
  require(pscl)
  s <- summary(model)
  coefficient.names <- rownames(s$coef)
  coefficients <- s$coef[, 1]
  standard.errors <- s$coef[, 2]
  significance <- s$coef[, 4]
  lik <- logLik(model)[1]
  aic <- AIC(model)
  bic <- BIC(model)
  R2 <-pR2(model)[[4]]
  dev <- deviance(model)
  n <- nobs(model)
  gof <- numeric()
  gof.names <- character()
  gof.decimal <- logical()
  if (include.pseudoR2 == TRUE) {
    gof <- c(gof, R2)
    gof.names <- c(gof.names, "Pseudo R2")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.aic == TRUE) {
    gof <- c(gof, aic)
    gof.names <- c(gof.names, "AIC")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.bic == TRUE) {
    gof <- c(gof, bic)
    gof.names <- c(gof.names, "BIC")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.loglik == TRUE) {
    gof <- c(gof, lik)
    gof.names <- c(gof.names, "Log Likelihood")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.deviance == TRUE) {
    gof <- c(gof, dev)
    gof.names <- c(gof.names, "Deviance")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.nobs == TRUE) {
    gof <- c(gof, n)
    gof.names <- c(gof.names, "Num. obs.")
    gof.decimal <- c(gof.decimal, FALSE)
  }
  tr <- createTexreg(coef.names = coefficient.names, coef = coefficients, 
                     se = standard.errors, pvalues = significance, gof.names = gof.names, 
                     gof = gof, gof.decimal = gof.decimal)
  return(tr)
}



extract.mlogit2 <- function (model, include.aic = FALSE, include.loglik = TRUE, include.R2 = TRUE, include.nobs = TRUE)
{
  s <- summary(model)
  coefs <- s$CoefTable[, 1]
  rn <- rownames(s$CoefTable)
  se <- s$CoefTable[, 2]
  pval <- s$CoefTable[, 4]
  gof <- numeric()
  gof.names <- character()
  gof.decimal <- logical()
  if (include.R2 == TRUE) {
    gof <-  round(s$mfR2[1],3)
    gof.names <- c(gof.names, "Pseudo R2")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.aic == TRUE) {
    gof <- c(gof, AIC(model))
    gof.names <- c(gof.names, "AIC")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.loglik == TRUE) {
    gof <- c(gof, logLik(model)[1])
    gof.names <- c(gof.names, "Log Likelihood")
    gof.decimal <- c(gof.decimal, TRUE)
  }
  if (include.nobs == TRUE) {
    gof <- c(gof, nrow(s$residuals))
    gof.names <- c(gof.names, "Num. obs.")
    gof.decimal <- c(gof.decimal, FALSE)
  }
  tr <- createTexreg(coef.names = rn, coef = coefs, se = se, 
                     pvalues = pval, gof.names = gof.names, gof = gof, gof.decimal = gof.decimal)
  return(tr)
}



texreg2 <- function (l, file = NULL, single.row = FALSE, stars = c(0.001,0.01, 0.05), custom.model.names = NULL, custom.coef.names = NULL, 
          custom.gof.names = NULL, custom.note = NULL, digits = 2, 
          leading.zero = TRUE, symbol = "\\cdot", override.coef = 0, 
          override.se = 0, override.pvalues = 0, override.ci.low = 0, 
          override.ci.up = 0, omit.coef = NULL, reorder.coef = NULL, 
          reorder.gof = NULL, ci.force = FALSE, ci.force.level = 0.95, 
          ci.test = 0, groups = NULL, custom.columns = NULL, custom.col.pos = NULL, 
          bold = 0, center = TRUE, caption = "Statistical models", 
          caption.above = FALSE, label = "table:coefficients", booktabs = FALSE, 
          dcolumn = FALSE, sideways = FALSE, longtable = FALSE, use.packages = TRUE, 
          table = TRUE, no.margin = FALSE, fontsize = NULL, scalebox = NULL, 
          float.pos = "", ...) {
  
  
  stars <- check.stars(stars)
  if (dcolumn == TRUE && bold > 0) {
    dcolumn <- FALSE
    msg <- paste("The dcolumn package and the bold argument cannot be used at", 
                 "the same time. Switching off dcolumn.")
    if (length(stars) > 1 || stars == TRUE) {
      warning(paste(msg, "You should also consider setting stars = 0."))
    }
    else {
      warning(msg)
    }
  }
  if (longtable == TRUE && sideways == TRUE) {
    sideways <- FALSE
    msg <- paste("The longtable package and sideways environment cannot be", 
                 "used at the same time. You may want to use the pdflscape package.", 
                 "Switching off sideways.")
    warning(msg)
  }
  if (longtable == TRUE && !(float.pos %in% c("", "l", "c", 
                                              "r"))) {
    float.pos <- ""
    msg <- paste("When the longtable environment is used, the float.pos", 
                 "argument can only take one of the \"l\", \"c\", \"r\", or \"\"", 
                 "(empty) values. Setting float.pos = \"\".")
    warning(msg)
  }
  if (longtable == TRUE && !is.null(scalebox)) {
    scalebox <- NULL
    warning(paste("longtable and scalebox are not compatible. Setting", 
                  "scalebox = NULL."))
  }
  models <- get.data(l, ...)
  gof.names <- get.gof(models)
  models <- override(models, override.coef, override.se, override.pvalues, 
                     override.ci.low, override.ci.up)
  models <- ciforce(models, ci.force = ci.force, ci.level = ci.force.level)
  models <- correctDuplicateCoefNames(models)
  gofs <- aggregate.matrix(models, gof.names, custom.gof.names, 
                           digits, returnobject = "gofs")
  m <- aggregate.matrix(models, gof.names, custom.gof.names, 
                        digits, returnobject = "m")
  decimal.matrix <- aggregate.matrix(models, gof.names, custom.gof.names, 
                                     digits, returnobject = "decimal.matrix")
  m <- customnames(m, custom.coef.names)
  m <- rearrangeMatrix(m)
  m <- as.data.frame(m)
  m <- omitcoef(m, omit.coef)
  m <- replaceSymbols(m)
  modnames <- modelnames(l, models, custom.model.names)
  m <- reorder(m, reorder.coef)
  gofs <- reorder(gofs, reorder.gof)
  decimal.matrix <- reorder(decimal.matrix, reorder.gof)
  lab.list <- c(rownames(m), gof.names)
  lab.length <- 0
  for (i in 1:length(lab.list)) {
    if (nchar(lab.list[i]) > lab.length) {
      lab.length <- nchar(lab.list[i])
    }
  }
  ci <- logical()
  for (i in 1:length(models)) {
    if (length(models[[i]]@se) == 0 && length(models[[i]]@ci.up) > 
        0) {
      ci[i] <- TRUE
    }
    else {
      ci[i] <- FALSE
    }
  }
  output.matrix <- outputmatrix(m, single.row, neginfstring = "\\multicolumn{1}{c}{$-\\infty$}", 
                                posinfstring = "\\multicolumn{1}{c}{$\\infty$}", leading.zero, 
                                digits, se.prefix = " \\; (", se.suffix = ")", star.prefix = "^{", 
                                star.suffix = "}", star.char = "*", stars, dcolumn = dcolumn, 
                                symbol, bold, bold.prefix = "\\mathbf{", bold.suffix = "}", 
                                ci = ci, semicolon = ";\\ ", ci.test = ci.test)
  output.matrix <- grouping(output.matrix, groups, indentation = "\\quad ", 
                            single.row = single.row, prefix = "", suffix = "")
  gof.matrix <- gofmatrix(gofs, decimal.matrix, dcolumn = TRUE, 
                          leading.zero, digits)
  output.matrix <- rbind(output.matrix, gof.matrix)
  output.matrix <- customcolumns(output.matrix, custom.columns, 
                                 custom.col.pos, single.row = single.row, numcoef = nrow(m), 
                                 groups = groups, modelnames = FALSE)
  coltypes <- customcolumnnames(modnames, custom.columns, custom.col.pos, 
                                types = TRUE)
  modnames <- customcolumnnames(modnames, custom.columns, custom.col.pos, 
                                types = FALSE)
  coldef <- ""
  if (no.margin == FALSE) {
    margin.arg <- ""
  }
  else {
    margin.arg <- "@{}"
  }
  coefcount <- 0
  for (i in 1:length(modnames)) {
    if (coltypes[i] == "coef") {
      coefcount <- coefcount + 1
    }
    if (single.row == TRUE && coltypes[i] == "coef") {
      if (ci[coefcount] == FALSE) {
        separator <- ")"
      }
      else {
        separator <- "]"
      }
    }
    else {
      separator <- "."
    }
    if (coltypes[i] %in% c("coef", "customcol")) {
      alignmentletter <- "c"
    }
    else if (coltypes[i] == "coefnames") {
      alignmentletter <- "l"
    }
    if (dcolumn == FALSE) {
      coldef <- paste0(coldef, alignmentletter, margin.arg, 
                       " ")
    }
    else {
      if (coltypes[i] != "coef") {
        coldef <- paste0(coldef, alignmentletter, margin.arg, 
                         " ")
      }
      else {
        if (single.row == TRUE) {
          dl <- compute.width(output.matrix[, i], left = TRUE, 
                              single.row = TRUE, bracket = separator)
          dr <- compute.width(output.matrix[, i], left = FALSE, 
                              single.row = TRUE, bracket = separator)
        }
        else {
          dl <- compute.width(output.matrix[, i], left = TRUE, 
                              single.row = FALSE, bracket = separator)
          dr <- compute.width(output.matrix[, i], left = FALSE, 
                              single.row = FALSE, bracket = separator)
        }
        coldef <- paste0(coldef, "D{", separator, "}{", 
                         separator, "}{", dl, separator, dr, "}", margin.arg, 
                         " ")
      }
    }
  }
  string <- "\n"
  if (use.packages == TRUE) {
    if (sideways == TRUE & table == TRUE) {
      string <- paste0(string, "\\usepackage{rotating}\n")
    }
    if (booktabs == TRUE) {
      string <- paste0(string, "\\usepackage{booktabs}\n")
    }
    if (dcolumn == TRUE) {
      string <- paste0(string, "\\usepackage{dcolumn}\n")
    }
    if (longtable == TRUE) {
      string <- paste0(string, "\\usepackage{longtable}\n")
    }
    if (dcolumn == TRUE || booktabs == TRUE || sideways == 
        TRUE || longtable == TRUE) {
      string <- paste0(string, "\n")
    }
  }
  if (longtable == TRUE) {
    if (center == TRUE) {
      string <- paste0(string, "\\begin{center}\n")
    }
    if (!is.null(fontsize)) {
      string <- paste0(string, "\\begin{", fontsize, "}\n")
    }
    if (float.pos == "") {
      string <- paste0(string, "\\begin{longtable}{", coldef, 
                       "}\n")
    }
    else {
      string <- paste0(string, "\\begin{longtable}[", float.pos, 
                       "]\n")
    }
  }
  else {
    if (table == TRUE) {
      if (sideways == TRUE) {
        t <- "sideways"
      }
      else {
        t <- ""
      }
      if (float.pos == "") {
        string <- paste0(string, "\\begin{", t, "table}\n")
      }
      else {
        string <- paste0(string, "\\begin{", t, "table}[", 
                         float.pos, "]\n")
      }
      if (caption.above == TRUE) {
        string <- paste0(string, "\\caption{", caption, 
                         "}\n")
      }
      if (center == TRUE) {
        string <- paste0(string, "\\begin{center}\n")
      }
      if (!is.null(fontsize)) {
        string <- paste0(string, "\\begin{", fontsize, 
                         "}\n")
      }
      if (!is.null(scalebox)) {
        string <- paste0(string, "\\scalebox{", scalebox, 
                         "}{\n")
      }
    }
    string <- paste0(string, "\\begin{tabular}{", coldef, 
                     "}\n")
  }
  tablehead <- ""
  if (booktabs == TRUE) {
    tablehead <- paste0(tablehead, "\\toprule\n")
  }
  else {
    tablehead <- paste0(tablehead, "\\hline\n")
  }
  tablehead <- paste0(tablehead, modnames[1])
  if (dcolumn == TRUE) {
    for (i in 2:length(modnames)) {
      if (coltypes[i] != "coef") {
        tablehead <- paste0(tablehead, " & ", modnames[i])
      }
      else {
        tablehead <- paste0(tablehead, " & \\multicolumn{1}{c}{", 
                            modnames[i], "}")
      }
    }
  }
  else {
    for (i in 2:length(modnames)) {
      tablehead <- paste0(tablehead, " & ", modnames[i])
    }
  }
  if (booktabs == TRUE) {
    tablehead <- paste0(tablehead, " \\\\\n", "\\midrule\n")
  }
  else {
    tablehead <- paste0(tablehead, " \\\\\n", "\\hline\n")
  }
  if (longtable == FALSE) {
    string <- paste0(string, tablehead)
  }
  if (is.null(stars)) {
    snote <- ""
  }
  else if (any(ci == FALSE)) {
    st <- sort(stars)
    if (length(unique(st)) != length(st)) {
      stop("Duplicate elements are not allowed in the stars argument.")
    }
    if (length(st) == 4) {
      snote <- paste0("$^{***}p<", st[1], "$, $^{**}p<", 
                      st[2], "$, $^*p<", st[3], "$, $^{", symbol, "}p<", 
                      st[4], "$")
    }
    else if (length(st) == 3) {
      snote <- paste0("$^{***}p<", st[1], "$, $^{**}p<", 
                      st[2], "$, $^*p<", st[3], "$")
    }
    else if (length(st) == 2) {
      snote <- paste0("$^{**}p<", st[1], "$, $^*p<", st[2], 
                      "$")
    }
    else if (length(st) == 1) {
      snote <- paste0("$^*p<", st[1], "$")
    }
    else {
      snote <- ""
    }
    if (is.numeric(ci.test) && !is.na(ci.test) && nchar(snote) > 
        0 && any(ci)) {
      snote <- paste(snote, "(or", ci.test, "outside the confidence interval).")
    }
    else if (is.numeric(ci.test) && !is.na(ci.test) && any(ci)) {
      snote <- paste("$^*$", ci.test, "outside the confidence interval")
    }
  }
  else if (is.numeric(ci.test) && !is.na(ci.test)) {
    snote <- paste("$^*$", ci.test, "outside the confidence interval")
  }
  else {
    snote <- ""
  }
  if (is.null(fontsize)) {
    notesize <- "scriptsize"
  }
  else if (fontsize == "tiny" || fontsize == "scriptsize" || 
           fontsize == "footnotesize" || fontsize == "small") {
    notesize <- "tiny"
  }
  else if (fontsize == "normalsize") {
    notesize <- "scriptsize"
  }
  else if (fontsize == "large") {
    notesize <- "footnotesize"
  }
  else if (fontsize == "Large") {
    notesize <- "small"
  }
  else if (fontsize == "LARGE") {
    notesize <- "normalsize"
  }
  else if (fontsize == "huge") {
    notesize <- "large"
  }
  else if (fontsize == "Huge") {
    notesize <- "Large"
  }
  if (is.null(custom.note)) {
    note <- paste0("\\multicolumn{", length(modnames), "}{l}{\\", 
                   notesize, "{", snote, "}}")
  }
  else if (custom.note == "") {
    note <- ""
  }
  else {
    note <- paste0("\\multicolumn{", length(modnames), "}{l}{\\", 
                   notesize, "{", custom.note, "}}")
    note <- gsub("%stars", snote, note, perl = TRUE)
  }
  if (longtable == TRUE) {
    note <- paste0(note, "\\\\\n")
  }
  else {
    note <- paste0(note, "\n")
  }
  if (booktabs == TRUE) {
    bottomline <- "\\bottomrule\n"
  }
  else {
    bottomline <- "\\hline\n"
  }
  if (longtable == TRUE) {
    if (caption.above == TRUE) {
      string <- paste0(string, "\\caption{", caption, "}\n", 
                       "\\label{", label, "}\\\\\n", tablehead, "\\endfirsthead\n", 
                       tablehead, "\\endhead\n", bottomline, "\\endfoot\n", 
                       bottomline, note, "\\endlastfoot\n")
    }
    else {
      string <- paste0(string, tablehead, "\\endfirsthead\n", 
                       tablehead, "\\endhead\n", bottomline, "\\endfoot\n", 
                       bottomline, note, "\\caption{", caption, "}\n", 
                       "\\label{", label, "}\n", "\\endlastfoot\n")
    }
  }
  max.lengths <- numeric(length(output.matrix[1, ]))
  for (i in 1:length(output.matrix[1, ])) {
    max.length <- 0
    for (j in 1:length(output.matrix[, 1])) {
      if (nchar(output.matrix[j, i]) > max.length) {
        max.length <- nchar(output.matrix[j, i])
      }
    }
    max.lengths[i] <- max.length
  }
  for (i in 1:length(output.matrix[, 1])) {
    for (j in 1:length(output.matrix[1, ])) {
      nzero <- max.lengths[j] - nchar(output.matrix[i, 
                                                    j])
      zeros <- rep(" ", nzero)
      zeros <- paste(zeros, collapse = "")
      output.matrix[i, j] <- paste0(output.matrix[i, j], 
                                    zeros)
    }
  }
  for (i in 1:(length(output.matrix[, 1]) - length(gof.names))) {
    for (j in 1:length(output.matrix[1, ])) {
      string <- paste0(string, output.matrix[i, j])
      if (j == length(output.matrix[1, ])) {
        string <- paste0(string, " \\\\\n")
      }
      else {
        string <- paste0(string, " & ")
      }
    }
  }
  if (length(gof.names) > 0) {
    if (booktabs == TRUE) {
      string <- paste0(string, "\\midrule\n")
    }
    else {
      string <- paste0(string, "\\hline\n")
    }
    for (i in (length(output.matrix[, 1]) - (length(gof.names) - 
                                             1)):(length(output.matrix[, 1]))) {
      for (j in 1:length(output.matrix[1, ])) {
        string <- paste0(string, output.matrix[i, j])
        if (j == length(output.matrix[1, ])) {
          string <- paste0(string, " \\\\\n")
        }
        else {
          string <- paste0(string, " & ")
        }
      }
    }
  }
  if (longtable == FALSE) {
    string <- paste0(string, bottomline)
    string <- paste0(string, note, "\\end{tabular}\n")
  }
  if (longtable == TRUE) {
    string <- paste0(string, "\\end{longtable}\n")
    if (!is.null(fontsize)) {
      string <- paste0(string, "\\end{", fontsize, "}\n")
    }
    if (center == TRUE) {
      string <- paste0(string, "\\end{center}\n")
    }
  }
  else if (table == TRUE) {
    if (!is.null(fontsize)) {
      string <- paste0(string, "\\end{", fontsize, "}\n")
    }
    if (!is.null(scalebox)) {
      string <- paste0(string, "}\n")
    }
    if (caption.above == FALSE) {
      string <- paste0(string, "\\caption{", caption, "}\n")
    }
    string <- paste0(string, "\\label{", label, "}\n")
    if (center == TRUE) {
      string <- paste0(string, "\\end{center}\n")
    }
    if (sideways == TRUE) {
      t <- "sideways"
    }
    else {
      t <- ""
    }
    string <- paste0(string, "\\end{", t, "table}\n")
  }
  if (is.null(file) || is.na(file)) {
    class(string) <- c("character", "texregTable")
    return(string)
  }
  else if (!is.character(file)) {
    stop("The 'file' argument must be a character string.")
  }
  else {
    sink(file)
    cat(string)
    sink()
    message(paste0("The table was written to the file '", 
                   file, "'.\n"))
  }
}
environment(texreg2) = environment(texreg)



grid_arrange_shared_legend <- function(..., ncol = length(list(...)), nrow = 1, position = c("bottom", "right")) {
  
  plots <- list(...)
  position <- match.arg(position)
  g <- ggplotGrob(plots[[1]] + theme(legend.position = position))$grobs
  legend <- g[[which(sapply(g, function(x) x$name) == "guide-box")]]
  lheight <- sum(legend$height)
  lwidth <- sum(legend$width)
  gl <- lapply(plots, function(x) x + theme(legend.position="none"))
  gl <- c(gl, ncol = ncol, nrow = nrow)
  
  combined <- switch(position,
                     "bottom" = arrangeGrob(do.call(arrangeGrob, gl),
                                            legend,
                                            ncol = 1,
                                            heights = unit.c(unit(1, "npc") - lheight, lheight)),
                     "right" = arrangeGrob(do.call(arrangeGrob, gl),
                                           legend,
                                           ncol = 2,
                                           widths = unit.c(unit(1, "npc") - lwidth, lwidth)))
  
  grid.newpage()
  grid.draw(combined)
  
  # return gtable invisibly
  invisible(combined)
  
}



generate_data_sim <- function(data_path, use = "min")
{
  datasets = load_and_clean(data_path, dataname = "filter/data_ATT_2011_filtered_after_duration_var_added_new.csv")
  if (use == "max"){data = datasets[[1]]}
  if (use == "min"){data = datasets[[2]]}
  list_var = c("ident", "annee",  "sexe", "c_cir_2011", "generation", "an_aff", "grade", 
               "E_exam", "E_choice", "D_exam", "D_choice",
               "time", "anciennete_dans_echelon", "echelon", "ib")
  data = data[which(data$left_censored == F  & data$annee == 2011 & data$generation < 1990),
              list_var ]
  data_sim  =  create_variables(data) 
  return(data_sim)
}

generate_data_output <- function(data_path)
{
  dataname = "filter/data_ATT_2011_filtered_after_duration_var_added_new.csv"
  filename = paste0(data_path, dataname)
  data_long = read.csv(filename)
  data_long$grade = data_long$c_cir
  data_long$situation = data_long$next_grade_situation
  list_var = c("ident", "annee", "c_cir_2011", "sexe", "generation", "grade","ib", "echelon", "situation")
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



predict_next_year_MNL <- function(data_sim, model, modelname)
{
  adhoc <- sample(c("no_exit",   "exit_next", "exit_oth"), nrow(data_sim), replace=TRUE, prob = c(0.2, 0.2, 0.6))
  data_sim$next_year <-adhoc
  data_sim$grade <-as.character(data_sim$grade)
  # Prediction for AT grade
  data_AT = data_sim[which(is.element(data_sim$grade, c("TTH1","TTH2", "TTH3", "TTH4"))), ]
  data_predict_MNL <- mlogit.data(data_AT, shape = "wide", choice = "next_year")  
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





predict_next_year_byG <- function(data_sim, list_model, modelname)
{
  adhoc <- sample(c("no_exit",   "exit_next", "exit_oth"), nrow(data_sim), replace=TRUE, prob = c(0.2, 0.2, 0.6))
  data_sim$next_year <-adhoc
  data_sim$grade <-as.character(data_sim$grade)
  # Prediction by grade
  n = names(data_sim)
  data_merge = as.data.frame(setNames(replicate(length(n),numeric(0), simplify = F), n))
  list_grade = c("TTH1","TTH2", "TTH3", "TTH4")
  for (g in 1:length(list_grade))
  {
    data = data_sim[which(data_sim$grade == list_grade[g]), ]
    model = list_model[[g]]
    if (list_grade[g] != "TTH4")
    {
      data_predict = mlogit.data(data, shape = "wide", choice = "next_year")  
      prob     <- predict(model, data_predict ,type = "response") 
      data$yhat = mapply(tirage_next_year_MNL, prob[,1], prob[,2], prob[,3])
    }
    if (list_grade[g] == "TTH4")
    {
      data_predict = data
      prob     <- predict(model, data_predict ,type = "response") 
      pred     <- as.numeric(mapply(tirage, prob))
      data$yhat = ifelse(pred == 1, "exit_oth", "no_exit")
    }
    
    data_merge = rbind(data_merge, data)
  }
  
  if (length(unique(data_sim$grade)) > 4)
  {
    data_noAT = data_sim[which(!is.element(data_sim$grade, list_grade)), ]
    data_noAT$yhat = "no_exit" 
    data_sim = rbind(data_merge, data_noAT)  
  }
  else{
    data_sim =  data_merge 
  }
  
  data_sim = data_sim[order(data_sim$ident), ]
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
  if (length(data_sim$ident) != length(simul_py$ident) | length(which(is.na(simul_py$ib)) >0 )  | length(which(is.na(simul_py$grade)) >0 ))
  {
    
    list_pbl_id1 = unique(setdiff(data_sim$ident, simul_py$ident))
    print(paste0("Il y a ",length(list_pbl_id1)," présents dans data_sim et absent dans simul"))
    
    list_pbl_id2 = unique(setdiff(simul_py$ident, data_sim$ident))
    print(paste0("Il y a ",length(list_pbl_id2)," présents dans simul et absent dans data_sim"))
    
    list_pbl_ib = unique(simul_py$ident[which(is.na(simul_py$ib))])
    print(paste0("Il y a ",length(list_pbl_ib)," individus dans la base simul  avec ib = NA"))
    
    list_pbl_grade = unique(simul_py$ident[which(is.na(simul_py$grade) | simul_py$grade == "nan")])
    print(paste0("Il y a ",length(list_pbl_grade)," individus dans la simul  avec grade = NA"))
    
    deleted_id = Reduce(union, list(list_pbl_id1, list_pbl_id2, list_pbl_ib, list_pbl_grade))
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
  
  return(data_merge)
}


save_results_simul <- function(output, data_sim, modelname)
{
  var = c("grade", "anciennete_dans_echelon", "echelon", "ib", "situation", "I_bothC", "time")
  new_var = paste0(c("grade", "anciennete_dans_echelon", "echelon", "ib", "situation", "I_bothC"), "_", modelname )
  data_sim[, new_var] = data_sim[, var]
  add = data_sim[, c("ident", "annee", new_var)]
  # Merge
  output = rbind(output, add)
  output = output[order(output$ident, output$annee),]
  return(output)
}



# Predicted probabilities -------------------------------------------------


plot_comp_predicted_prob = function(data, data_estim, list_models, model_names, grade = "Tous", xvariable = "duration")
{
  stopifnot(is.element(grade, c("Tous", "TTH1", "TTH2", "TTH3", "TTH4")))  
  stopifnot(length(list_models) == length(model_names)) 
  # Obs  
  data$xvariable =   data[, xvariable]
  data$no_exit   = ifelse(data$next_year == "no_exit",   1, 0)
  data$exit_next = ifelse(data$next_year == "exit_next", 1, 0)
  data$exit_oth  = ifelse(data$next_year == "exit_oth",  1, 0)
  if (grade != "Tous"){data = data[which(data$grade == grade),]}
  df <- aggregate(cbind(no_exit, exit_next, exit_oth ) ~ xvariable, data, FUN= "mean" )
  df$mod = "obs"
  # Pred
  for (m in 1:length(list_models))
  {
    if (grade != "Tous"){data_estim = data_estim[which(data_estim$grade == grade),]}  
    prob <- as.data.frame(predict(list_models[[m]] , data_estim ,type = "response"))  
    prob <- cbind(prob, data[, c("grade", xvariable)]) 
    prob$xvariable =   prob[, xvariable]
    mean <- aggregate(cbind(no_exit, exit_next, exit_oth ) ~ xvariable, prob, FUN= "mean" )
    mean$mod = model_names[m]
    df = rbind(df, mean)
  }
  df <- melt(df, id.vars = c(1,5), value.name = "probability")
  ggplot(df, aes(x = xvariable, y = probability, colour = mod)) + 
    geom_line( size = 1) + facet_grid(variable ~ ., scales = "free") + theme_bw() + 
    labs(x = xvariable) + labs(colour = "Modèles")
}




