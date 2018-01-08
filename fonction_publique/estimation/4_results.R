

#################################  Simulation diagnosis ###############################
# Comparing predicted and observed outcomes 
# I. Grade : we compare observed and simulated exit from initial grade by grade and destination
# II. IB
 

### 0. Initialisation ####

source(paste0(wd, "0_Outils_CNRACL.R")) 
# Load results
load(paste0(simul_path, "predictions7_min.Rdata"))

## NEW FILTER: à déplacer dans select_data
list_id = unique(output_global$ident[which(output_global$echelon == -1)])
print(paste0("Individus avec échelon = -1 :  ", length(list_id)))
output_global = output_global[which(!is.element(output_global$ident, list_id)), ]

list_id = unique(output_global$ident[which(output_global$generation >= 1990)])
print(paste0("Individus nés après 1990:  ", length(list_id)))
output_global = output_global[which(!is.element(output_global$ident, list_id)), ]

output_global$next_ib = ave(output_global$ib, output_global$ident, FUN = shift1)
output_global$gain_ib = (output_global$next_ib - output_global$ib)/output_global$ib
list_id = unique(output_global$ident[which(output_global$gain_ib >= 0.2 & !is.na(output_global$gain_ib))])
print(paste0("Individus avec une hausse d'ib de +20% :  ", length(list_id)))
output_global = output_global[which(!is.element(output_global$ident, list_id)), ]
      



########## I. Prediction des sorties de grades  ##########


## I.1 Survie dans le grade ####

# Obs
exit_obs      = extract_exit(output_global, "situation")
exit_obs_TTH1 = extract_exit(output_global[which(output_global$c_cir_2011 == "TTH1"), ], "situation")
exit_obs_TTH2 = extract_exit(output_global[which(output_global$c_cir_2011 == "TTH2"), ], "situation")
exit_obs_TTH3 = extract_exit(output_global[which(output_global$c_cir_2011 == "TTH3"), ], "situation")
exit_obs_TTH4 = extract_exit(output_global[which(output_global$c_cir_2011 == "TTH4"), ], "situation")
limits = c(0.5, 0.5, 0.3, 0.5)
p_obs = plot_share(exit_obs, plot = F, title = "Obs")
p_obs_TTH1 =  plot_share(exit_obs_TTH1, plot = F, title = "Obs")
p_obs_TTH2 =  plot_share(exit_obs_TTH2, plot = F, title = "Obs")
p_obs_TTH3 =  plot_share(exit_obs_TTH3, plot = F, title = "Obs")
p_obs_TTH4 =  plot_share(exit_obs_TTH4, plot = F, title = "Obs")
# Sim
list_models = c("MNL_2", "MNL_3", "BG_1","MS_1")
for (m in (1:length(list_models)))
{
var = paste0("situation_", list_models[m])  
exit     = extract_exit(output_global, exit_var = var)
p = plot_share(exit, plot = F, title =  list_models[m])
assign(paste0("exit_",  list_models[m]), exit)  
assign(paste0("p_",  list_models[m]), p)
list_grade =c("TTH1", "TTH2", "TTH3", "TTH4")
  for (g in 1:length(list_grade))
  {
    exit = extract_exit(output_global[which(output_global$c_cir_2011 == list_grade[g]), ], var)
    p = plot_share(exit, plot = F, title = list_models[m])
    assign(paste0("exit_", list_models[m],"_",list_grade[g]), exit)  
    assign(paste0("p_", list_models[m],"_",list_grade[g]), p)  
  }
}
  

pdf(paste0(fig_path,"exit_comp_TTH1.pdf"), onefile=FALSE)
grid_arrange_shared_legend(p_obs_TTH1,  p_MNL_2_TTH1, p_MNL_3_TTH1, p_BG_1_TTH1, p_MS_1_TTH1, ncol = 5, nrow = 1)
dev.off()

pdf(paste0(fig_path,"exit_comp_TTH2.pdf"), onefile=FALSE)
grid_arrange_shared_legend(p_obs_TTH2, p_MNL_2_TTH2, p_MNL_3_TTH2, p_BG_1_TTH2, p_MS_1_TTH2,  ncol = 5, nrow = 1)
dev.off()

pdf(paste0(fig_path,"exit_comp_TTH3.pdf"), onefile=FALSE)
grid_arrange_shared_legend(p_obs_TTH3, p_MNL_2_TTH3, p_MNL_3_TTH3, p_BG_1_TTH3, p_MS_1_TTH3,  ncol = 5, nrow = 1)
dev.off()

pdf(paste0(fig_path,"exit_comp_TTH4.pdf"), onefile=FALSE)
grid_arrange_shared_legend(p_obs_TTH4, p_MNL_2_TTH4, p_MNL_3_TTH4, p_BG_1_TTH4, p_MS_1_TTH4,  ncol = 5, nrow = 1)
dev.off()


## I.2 Caractéristiques des individus changeant de grade ####


# Caracteristics of movers
movers_characteristics = function(data, exit_var)
{  
  data = data[which(data$annee == 2011),]

  data$exit = as.character(data[, exit_var])
  data$cond = data[, "I_bothC_MNL_1"]
  data$age = 2011 - data$generation
  data$femme =ifelse(data$sexe == "F", 1, 0)
  
  table_movers = numeric(22)
  # All
  table_movers[1] = 100*length(which(data$exit[] == "exit_next"))/length(data$exit[])
  table_movers[2] = 100*length(which(data$exit[] == "exit_oth"))/length(data$exit[])                              
  # Women
  list = which(data$exit == "exit_next")
  table_movers[3] = 100*mean(data$femme[list])
  list = which(data$exit == "exit_oth")
  table_movers[4] = 100*mean(data$femme[list])
  # Age
  list = which(data$exit == "exit_next")
  table_movers[5] = mean(data$age[list])
  list = which(data$exit == "exit_oth")
  table_movers[6] = mean(data$age[list])
  # TTH1
  list = which(data$c_cir_2011 == "TTH1")
  table_movers[7] = 100*length(which(data$exit[list] == "exit_next"))/length(data$exit[list])
  table_movers[8] = 100*length(which(data$exit[list] == "exit_oth"))/length(data$exit[list])  
  # TTH2
  list = which(data$c_cir_2011 == "TTH2")
  table_movers[9] = 100*length(which(data$exit[list] == "exit_next"))/length(data$exit[list])
  table_movers[10] = 100*length(which(data$exit[list] == "exit_oth"))/length(data$exit[list])  
  # TTH3
  list = which(data$c_cir_2011 == "TTH3")
  table_movers[11] = 100*length(which(data$exit[list] == "exit_next"))/length(data$exit[list])
  table_movers[12] = 100*length(which(data$exit[list] == "exit_oth"))/length(data$exit[list])  
  # TTH4
  list = which(data$c_cir_2011 == "TTH4")
  table_movers[13] = 100*length(which(data$exit[list] == "exit_next"))/length(data$exit[list])
  table_movers[14] = 100*length(which(data$exit[list] == "exit_oth"))/length(data$exit[list])  
  # IB distrib
  list = which(data$exit == "exit_next")
  table_movers[15] = mean(data$ib[list])
  table_movers[16:18] = as.numeric(quantile(data$ib[list])[2:4])
  list = which(data$exit == "exit_oth")
  table_movers[19] = mean(data$ib[list])
  table_movers[20:22] = as.numeric(quantile(data$ib[list])[2:4])
  # Ech when mov
  list =   which(data$exit == "exit_next")
  table_movers[23] = mean(data$echelon[list])
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH1")
  table_movers[24] = mean(data$echelon[list])
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH2")
  table_movers[25] = mean(data$echelon[list])
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH3")
  table_movers[26] = mean(data$echelon[list])
  # Condition remplies when exit next by grade
  list =   which(data$exit == "exit_next")
  table_movers[27] = mean(data$cond[list], na.rm = T)
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH1")
  table_movers[28] = mean(data$cond[list], na.rm = T)
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH2")
  table_movers[29] = mean(data$cond[list], na.rm = T)
  list =   which(data$exit == "exit_next" & data$c_cir_2011 == "TTH3")
  table_movers[30] = mean(data$cond[list], na.rm = T)
  return(table_movers)
}

list1 = which(output_global$situation == "exit_next" & output_global$annee == 2011 & output_global$c_cir_2011 == "TTH2")
list2 = which(output_global$situation_BG_1 == "exit_next" & output_global$annee == 2011 & output_global$c_cir_2011 == "TTH2")
table(output_global$echelon[list1])/length(list1)
table(output_global$echelon[list2])/length(list2)

table_obs =  movers_characteristics(data = output_global, exit_var = "situation")
for (m in c("MNL_2", "MNL_3", "BG_1","MS_1"))
{
  var = paste0("situation_", m)  
  table     = movers_characteristics(data = output_global, exit_var = var)
  assign(paste0("table_", m), table)  
}

table_movers = cbind(table_obs, table_MNL_2, table_MNL_3, table_BG_1, table_MS_1)
colnames(table_movers) = c('Observed', "MNL\\_2", "MNL\\_3", "BG\\_1", "MS\\_1")
rownames(table_movers) = c("\\% exit next All", "\\% exit oth All", 
                           "\\% Women when exit next", "\\% Women when exit oth",
                           "Mean age when exit next", "Mean age  when exit oth",
                           "\\% exit next TTH1", "\\% exit oth TTH1", "\\% exit next TTH2", "\\% exit oth TTH2",
                           "\\% exit next TTH3", "\\% exit oth TTH3", "\\% exit next TTH4", "\\% exit oth TTH4",
                           "Mean IB when exit next", "Q1 IB when exit next", "Q2 IB when exit next","Q3 IB when exit next",
                           "Mean IB when exit oth", "Q1 IB when exit oth", "Q2 IB when exit oth","Q3 IB when exit oth",
                           "Mean echelon when exit next",  "Mean ech when exit next TTH1", "Mean ech when exit next TTH2", "Mean ech when exit next TTH3",
                           "\\% cond. choix when exit next",  "\\% cond. choix when exit next TTH1",
                           "\\% cond. choix when exit next  TTH2","\\% cond. choix when exit next  TTH3")

mdigit <- matrix(c(rep(2,(ncol(table_movers)+1)*14),rep(0,(ncol(table_movers)+1)*8)),
                 nrow = nrow(table_movers), ncol=ncol(table_movers)+1, byrow=T)                           
print(xtable(table_movers, nrow = nrow(table_movers), align = "l|c|cccc",
             ncol=ncol(table_movers)+1, byrow=T, digits = mdigit,
             caption = "Profil des changements de grade"),
      sanitize.text.function=identity,size="\\footnotesize", hline.after = c(0, 2, 4, 6, 8, 10, 12, 14, 18, 22, 26),
      only.contents=T, include.colnames = T,
      file = paste0(fig_path,"profile_movers.tex"))
      


## I.3 Proportion de départ vers le grade suivant en fonction de l'échelon et de la durée ####


# Proba de sortie vers grade next par grade et par échelon
subdata = output_global[which(output_global$annee == 2011 & output_global$c_cir_2011 != "TTH4"),]
subdata$situation_obs = subdata$situation
subdata$duration = 2011- subdata$annee_entry_min + 1

var = c("ident", "c_cir_2011", "echelon", "duration", "situation_obs", "situation_MNL_2",
        "situation_MNL_3", "situation_MS_1", "situation_MS_2", "situation_BG_1")
subdata = subdata[, var]
df <- melt(subdata, id.vars = c(1:4), value.name = "next_year",  variable.name = "model")
df$model = substring(df$model, 11)
df$exit = ifelse(df$next_year == "exit_next", 1, 0)


comp_exit_by_ech = function(df, save = F, list_models, n_col, legend = F, grade)
{
  df = df[which(df$c_cir_2011 == grade),]
  
  ech = seq(range(df$echelon)[1],range(df$echelon)[2])
  hazard = matrix(ncol = length(ech), nrow = length(list_models))
  effectif = numeric(length(ech))
  
  for (m in 1:length(list_models))
  {
  subdf = df[which(df$model == list_models[m]),] 
    for (e in 1:length(ech))
    {
    if (m ==1){effectif[e] = length(which(subdf$echelon == ech[e]))}
    hazard[m, e] =   length(which(subdf$echelon == ech[e] & subdf$exit == 1))/length(which(subdf$echelon == ech[e]))
    }
  }  
  par(mar = c(4,4,1,1))
  lim = c(0, max(hazard, na.rm = T))
  plot(ech, rep(NA, length(ech)), ylim = lim, xlab = "ECHELON", ylab = "% EXIT NEXT GRADE")
  for (m in 1:length(list_models))
  {
  lines(ech ,hazard[m, ], type = "l", lty = 1, lwd = 3, col = n_col[m])
  }
  par(new = T)
  plot(ech, effectif, type ="l", lty = 2, lwd = 1, axes=F, xlab=NA, ylab=NA)
  if (legend){legend("topleft", legend = c("Hazard", "Nb obs."), lwd = 3, lty = c(1,3), col = c("darkcyan", "black"), cex = 1.1)}
}  


comp_exit_by_dur = function(df, save = F, list_models = c("obs", "MNL_2", "MNL_3", "BG_1"), n_col, legend = F, grade)
{
  df = df[which(df$c_cir_2011 == grade),]
  
  dur = seq(range(df$duration)[1],range(df$duration)[2])
  hazard = matrix(ncol = length(dur), nrow = length(list_models))
  effectif = numeric(length(dur))
  
  for (m in 1:length(list_models))
  {
    subdf = df[which(df$model == list_models[m]),] 
    for (e in 1:length(dur))
    {
      if (m ==1){effectif[e] = length(which(subdf$duration == dur[e]))}
      hazard[m, e] =   length(which(subdf$duration == dur[e] & subdf$exit == 1))/length(which(subdf$duration == dur[e]))
    }
  }  
  par(mar = c(4,4,1,1))
  lim = c(0, max(hazard, na.rm = T))
  plot(dur, rep(NA, length(dur)), ylim = lim, xlab = "DUREE DANS LE GRADE", ylab = "% EXIT NEXT GRADE")
  for (m in 1:length(list_models))
  {
    lines(dur ,hazard[m, ], type = "l", lty = 1, lwd = 3, col = n_col[m])
  }
  par(new = T)
  plot(dur, effectif, type ="l", lty = 2, lwd = 1, axes=F, xlab=NA, ylab=NA)
  if (legend){legend("topleft", legend = c("Hazard", "Nb obs."), lwd = 3, lty = c(1,3), col = c("darkcyan", "black"), cex = 1.1)}
}  


list_models = c("obs", "MNL_2", "MNL_3", "MS_1", "BG_1")
list_names = list_models

n_col <- c("black", "#727272","#f1595f","#79c36a","#599ad3", "#f9a65a", "#9e66ab", "#cd7058","#d77fb3")
for (grade in c("TTH1", "TTH2", "TTH3"))
{
  pdf(paste0(fig_path, "comp_exit_pred_",grade,".pdf"))
  layout(matrix(c(1,2,3, 3), nrow=2,ncol=2, byrow=F), heights =  c(3,3), widths = c(4,1))
  # Graphe by ech
  comp_exit_by_ech(df, list_models = list_models, n_col = n_col, grade = grade)
  # Graphe by dur
  comp_exit_by_dur(df, list_models = list_models, n_col = n_col, grade = grade) 
  # Legend
  par(mar=c(0,0,0,0),font=1.5)
  plot.new()
  legend("left", legend=c(list_names, "Nb \nd'obs\n"), lty=c(rep(1, length(list_names)), 2), title = "Modèles",
         col=c(n_col[1:length(list_names)],"black"),lwd=3,cex=1.2, ncol=1, bty = "n")
  dev.off()
  
}





############ II. IB comparison #############

## II.1 Masse IB ####


table_masse_ib = function(data, var_ib, var_obs)
{
  data$var_ib = data[, var_ib]
  data$var_obs = data[, var_obs]
  
  print(paste0("Il y a ",(length(which(is.na(data$var_ib))))," obs avec ib = NA, que l'on supprime"  ))
  data = data[which(!is.na(data$var_ib)),]
  
  table = numeric(1)
  
  table[1] = sum(data$var_ib)/1e6
  table[2] = 100*(sum(data$var_ib)-sum(data$var_obs))/sum(data$var_obs)
  table[3] = sum(data$var_ib[which(data$annee == 2012)])/1e6
  table[4] = 100*(sum(data$var_ib[which(data$annee == 2012)]) - sum(data$var_obs[which(data$annee == 2012)]))/sum(data$var_obs[which(data$annee == 2012)])
  table[5] = sum(data$var_ib[which(data$annee == 2015)])/1e6
  table[6] = 100*(sum(data$var_ib[which(data$annee == 2015)]) - sum(data$var_obs[which(data$annee == 2015)]))/sum(data$var_obs[which(data$annee == 2015)])
  
  list_grade = c("TTH1", "TTH2", "TTH3", "TTH4")
  for (g in 1:length(list_grade))
  {
    list = which(data$c_cir_2011 == list_grade[g])
    table[6 + 4*(g-1)+1] = sum(data$var_ib[list])/1e6
    table[6 + 4*(g-1)+2] = 100*(sum(data$var_ib[list]) - sum(data$var_obs[list])) /sum(data$var_obs[list])
    list = which(data$c_cir_2011 == list_grade[g] & data$annee == 2015)
    table[6 + 4*(g-1)+3] = sum(data$var_ib[list])/1e6
    table[6 + 4*(g-1)+4] = 100*(sum(data$var_ib[list]) - sum(data$var_obs[list])) /sum(data$var_obs[list])
  }

  return(table)
}



obs = table_masse_ib(output_global, "ib", var_obs = "ib")
for (m in c("MNL_2", "MNL_3", "BG_1","MS_1"))
{
  table = table_masse_ib(data = output_global, var_ib = paste0("ib_", m), var_obs = "ib")
  assign(paste0("table_masse_", m), table)  
}

table = cbind(obs, table_masse_MNL_2, table_masse_MNL_3, table_masse_BG_1, table_masse_MS_1)
colnames(table) = c('Observed', "MNL\\_2", "MNL\\_3", "BG\\_1","MS\\_1")
rownames(table) = c("Masse totale 2011-2015 (en 1e6)", "\\% diff par rapport a obs", 
                    "Masse totale 2012 (en 1e6)",  "\\% diff 2012 par rapport a obs",
                    "Masse totale 2015 (en 1e6)",  "\\% diff 2015 par rapport a obs",
                    "Masse totale 2011-2015 TTH1 (en 1e6)", "\\% diff TTH1 par rapport a obs",
                    "Masse totale 2015 TTH1 (en 1e6)", "\\% diff TTH1 2015 par rapport a obs",
                    "Masse totale 2011-2015 TTH2 (en 1e6)", "\\% diff TTH2 par rapport a obs",
                    "Masse totale 2015 TTH2 (en 1e6)", "\\% diff TTH2 2015 par rapport a obs",
                    "Masse totale 2011-2015 TTH3 (en 1e6)", "\\% diff TTH3 par rapport a obs",
                    "Masse totale 2015 TTH3 (en 1e6)", "\\% diff TTH3 2015 par rapport a obs",
                    "Masse totale 2011-2015 TTH4 (en 1e6)", "\\% diff TTH4 par rapport a obs",
                    "Masse totale 2015 TTH4 (en 1e6)", "\\% diff TTH4 2015 par rapport a obs"
                      )

print(xtable(table,nrow = nrow(table), align = "l|c|cccc",
             ncol=ncol(table_movers)+1, byrow=T, digits = 2,
             caption = "Masses ib"),
      sanitize.text.function=identity,size="\\footnotesize", hline.after = c(0, 6, 10, 14, 18,22),
      only.contents=T, include.colnames = T)
      file = paste0(fig_path,"masses_ib.tex"))



table_gain_ib = function(data, var_ib, var_situation, var_grade, details = F)
{
  data$var_ib = data[, var_ib]
  data$var_situation = data[, var_situation]
  data$var_grade = data[, var_grade]
  data$next_ib = ave(data$var_ib, data$ident, FUN = shift1)
  data$gain_ib = data$next_ib - data$var_ib
  data$I_gain = ifelse(data$gain_ib >0, 1, 0)
  data$gain_ib_pct = 100*(data$gain_ib)/data$var_ib
  data = data[which(data$annee < 2015),]
  
  table = numeric(21)
  
  table[1] = mean(data$gain_ib, na.rm = T)
  table[2] = median(data$gain_ib_pct, na.rm = T)
  table[3] = 100*mean(data$I_gain, na.rm = T)
  
  list_grade = c("TTH1", "TTH2", "TTH3", "TTH4")
  for (g in 1:length(list_grade))
  {
    list = which(data$c_cir_2011 == list_grade[g])
    table[3*g+1] = mean(data$gain_ib[list], na.rm = T)
    table[3*g+2] = median(data$gain_ib_pct[list], na.rm = T)
    table[3*g+3] = 100*mean(data$I_gain[list], na.rm = T)
  }
  list = which(data$var_situation == "no_exit")
  table[16] = mean(data$gain_ib[list], na.rm = T)
  table[17] = 100*mean(data$I_gain[list], na.rm = T)
  list = which(data$var_situation == "exit_next")
  table[18] = mean(data$gain_ib[list], na.rm = T)
  table[19] = 100*mean(data$I_gain[list], na.rm = T)
  list = which(data$var_situation == "exit_oth")
  table[20] = mean(data$gain_ib[list], na.rm = T)
  table[21] = 100*mean(data$I_gain[list], na.rm = T)
  if (details)
  {
    for (g in 1:length(list_grade))
    {
    list = which(data$var_situation == "no_exit" & data$var_grade == list_grade[g])
    table[3*(g-1)+22] = mean(data$gain_ib[list], na.rm = T)
    list = which(data$var_situation == "exit_next"& data$var_grade == list_grade[g])
    table[3*(g-1)+23]= mean(data$gain_ib[list], na.rm = T)
    list = which(data$var_situation == "exit_oth"& data$var_grade == list_grade[g])
    table[3*(g-1)+24]= mean(data$gain_ib[list], na.rm = T)
    }
  }  
  return(table)
}


D = T
obs = table_gain_ib(output_global, "ib", "situation","grade",  details = D)
for (m in c("MNL_2", "MNL_3", "BG_1","MS_1"))
{
  table = table_gain_ib(data = output_global, var_ib = paste0("ib_", m), var_grade =  paste0("grade_", m),
                        var_situation =  paste0("situation_", m), details = D)
  assign(paste0("table_gain_", m), table)  
}

table = cbind(obs, table_gain_MNL_2, table_gain_MNL_3, table_gain_BG_1, table_gain_MS_1)
colnames(table) = c('Observed',  "MNL\\_2", "MNL\\_3", "BG\\_1","MS\\_1")
if (D == F)
{
rownames(table) = c("gain ib moyen", "gain ib median en \\%", "\\% gain ib > 0",
                     "gain ib moyen TTH1", "gain ib median en \\% TTH1", "\\% gain ib > 0  TTH1",
                     "gain ib moyen TTH2", "gain ib median en \\% TTH2", "\\% gain ib > 0  TTH2",
                     "gain ib moyen TTH3", "gain ib median en \\% TTH3", "\\% gain ib > 0 TTH3",
                     "gain ib moyen TTH4", "gain ib median en \\% TTH4", "\\% gain ib > 0 TTH4",
                     "gain ib moyen no\\_exit", "\\% gain ib > 0 no\\_exit",
                     "gain ib moyen exit\\_next", "\\% gain ib > 0 exit\\_next",
                     "gain ib moyen exit\\_oth", "\\% gain ib > 0 exit\\_oth"
                     )
}
if (D == T)
{
  rownames(table) = c("gain ib moyen", "gain ib median en \\%", "\\% gain ib > 0",
                      "gain ib moyen TTH1", "gain ib median en \\% TTH1", "\\% gain ib > 0  TTH1",
                      "gain ib moyen TTH2", "gain ib median en \\% TTH2", "\\% gain ib > 0  TTH2",
                      "gain ib moyen TTH3", "gain ib median en \\% TTH3", "\\% gain ib > 0 TTH3",
                      "gain ib moyen TTH4", "gain ib median en \\% TTH4", "\\% gain ib > 0 TTH4",
                      "gain ib moyen no\\_exit", "\\% gain ib > 0 no\\_exit",
                      "gain ib moyen exit\\_next", "\\% gain ib > 0 exit\\_next",
                      "gain ib moyen exit\\_oth", "\\% gain ib > 0 exit\\_oth",
                      "gain ib moyen no\\_exit TTH1" , "gain ib moyen exit\\_next TTH1", "gain ib moyen exit\\_oth TTH1",
                      "gain ib moyen no\\_exit TTH2" , "gain ib moyen exit\\_next TTH2", "gain ib moyen exit\\_oth TTH2",
                      "gain ib moyen no\\_exit TTH3" , "gain ib moyen exit\\_next TTH3", "gain ib moyen exit\\_oth TTH3",
                      "gain ib moyen no\\_exit TTH4" , "gain ib moyen exit\\_next TTH4", "gain ib moyen exit\\_oth TTH4"
                      
  )
  lines= c(0, 3, 6, 9, 12, 15, 17, 19, 21, 24, 27, 30, 33)
}


print(xtable(table,nrow = nrow(table), align = "l|c|cccc", caption = "Gains ib",
             ncol=ncol(table_movers)+1, byrow=T, digits = 2),
      sanitize.text.function=identity,size="\\footnotesize", hline.after = lines,
      only.contents=T, include.colnames = T,
      file = paste0(fig_path,"gain_ib.tex"))




## II. 3 Individuals  ####

# Ecart predit/observé pour grade et ib
list_pbl =  ""
for (m in c("MNL_2", "MNL_3", "BG_1","MS_1"))
{
var = paste0("ib_", m)
list_pbl_id = unique(output_global$ident[which(is.na(output_global[, var]))])
list_pbl = c(list_pbl, list_pbl_id)
list_pbl = unique(list_pbl)
}
output_global_cleared = output_global[which(!is.element(output_global$ident, list_pbl)),]


table_ind = function(data, var_ib, var_situation)
{
  data = data[which(data$annee > 2011), ]
  data$ib_obs = data[, "ib"]
  data$situation_obs = data[, "situation"]
  data$ib_sim = data[, var_ib]
  data$situation_sim = data[, var_situation]
  data$diff_ib = (data$ib_sim - data$ib_obs)
  data$diff_ib_abs = abs(data$ib_sim - data$ib_obs)
  
  table = numeric(12)
  
  # Proportion same situation
  table[1] = length(which(data$situation_obs == data$situation_sim))/length(data$situation_obs)
  list = which(data$situation_obs == "no_exit")
  table[2] = length(which(data$situation_obs[list] == data$situation_sim[list]))/length(list)
  list = which(data$situation_obs == "exit_next")
  table[3] = length(which(data$situation_obs[list] == data$situation_sim[list]))/length(list)
  list = which(data$situation_obs == "exit_oth")
  table[4] = length(which(data$situation_obs[list] == data$situation_sim[list]))/length(list)
  # Ecart ib  
  table[5] = mean(data$diff_ib, na.rm = T)
  table[6:8] = as.numeric(quantile(data$diff_ib, na.rm = T)[3:5])
  table[9] = mean(data$diff_ib_abs, na.rm = T)
  table[10:12] = as.numeric(quantile(data$diff_ib_abs, na.rm = T)[3:5])
  table[13] = mean(data$diff_ib[which(data$annee == 2012)], na.rm = T)
  table[14] = mean(data$diff_ib[which(data$annee == 2015)], na.rm = T)
  # Ecart moyen au carré
  table[15] = rmse(data$ib_sim, data$ib_obs)
  table[16] = rmse(data$ib_sim[which(data$c_cir_2011 == "TTH1")], data$ib_obs[which(data$c_cir_2011 == "TTH1")])
  table[17] = rmse(data$ib_sim[which(data$c_cir_2011 == "TTH2")], data$ib_obs[which(data$c_cir_2011 == "TTH2")])
  table[18] = rmse(data$ib_sim[which(data$c_cir_2011 == "TTH3")], data$ib_obs[which(data$c_cir_2011 == "TTH3")])
  table[19] = rmse(data$ib_sim[which(data$c_cir_2011 == "TTH4")], data$ib_obs[which(data$c_cir_2011 == "TTH4")])
  
  return(table)
}


for (m in c("MNL_2", "MNL_3", "BG_1","MS_1"))
{
  table = table_ind(data = output_global_cleared, var_ib = paste0("ib_", m) , var_situation = paste0("situation_", m) )
  assign(paste0("table_ind_", m), table)  
}

table_all = cbind(table_ind_MNL_2, table_ind_MNL_3, table_ind_BG_1, table_ind_MS_1)
colnames(table_all) = c("MNL\\_2", "MNL\\_3", "BG\\_1","MS\\_1")
rownames(table_all) = c("\\% bonne prediction etat", "\\% bonne prediction quand obs = no exit",
                        "\\% bonne prediction etat quand obs = exit next",
                        "\\% bonne prediction etat quand obs = exit oth",
                        "Ecart IB moyen", "Q2 ecart IB ","Q3 ecart IB ","Q4 ecart IB ",
                        "Ecart IB moyen (abs)", "Q2 ecart IB (abs)","Q3 ecart IB (abs)","Q4 ecart IB (abs)",
                        "Ecart IB moyen en 2011","Ecart IB moyen en 2014", 
                        "RMSE tous", "RMSE TTH1", "RMSE TTH2","RMSE TTH3", "RMSE TTH4")

print(xtable(table_all,nrow = nrow(table_all), align = "l|cccc", caption =  "Ecart observe simule",
             ncol=ncol(table_all)+1, byrow=T, digits = 2),
      sanitize.text.function=identity,size="\\footnotesize", hline.after = c(0, 4, 14, 19),
      only.contents=T, include.colnames = T,
      file = paste0(fig_path,"ecarts.tex"))







#### Ecart ib et echelon quand changement en 2011  ####

var = c("ident", "echelon", "grade", "ib", "situation","echelon_BG_1", "grade_BG_1", "ib_BG_1", "situation_BG_1")

comp_data = output_global[which(output_global$annee <= 2012),var]

list_ok = comp_data$ident[which(comp_data$annee == 2011 & comp_data$situation ==comp_data$situation_BG_1)]
comp_data = comp_data[which(is.element(comp_data$ident, list_ok)),]
comp_data$ech_obs = comp_data$echelon
comp_data$ech_sim = comp_data$echelon_BG_1
comp_data$var_ech = comp_data$ech_obs - comp_data$ech_sim
comp_data$ib_obs = comp_data$ib
comp_data$ib_sim = comp_data$ib_BG_1
comp_data$var_ib = comp_data$ib_obs - comp_data$ib_sim

comp2011 = comp_data[comp_data$annee == 2011,]
comp2012 = comp_data[comp_data$annee == 2012,]

table = matrix(ncol = 5, nrow = 8)

list_grade =  c("All", "TTH1", "TTH2", "TTH3", "TTH4")
for (g in 1:length(list_grade))
{
if (list_grade[g] == "All")
{
subcomp2011 = comp2011
subcomp2012 = comp2012
}
if (list_grade[g] != "All")
{
  subcomp2011 = comp2011[which(comp2011$c_cir_2011 == list_grade[g]),]
  subcomp2012 = comp2012[which(comp2011$c_cir_2011 == list_grade[g]),]
}
table[1,g] = mean(subcomp2012$var_ech)
table[2,g] = mean(subcomp2012$var_ib)
table[3,g] = mean(subcomp2012$var_ech[which(subcomp2011$situation == "no_exit")])
table[4,g] = mean(subcomp2012$var_ib[which(subcomp2011$situation == "no_exit")])
table[5,g] = mean(subcomp2012$var_ech[which(subcomp2011$situation == "exit_next")])
table[6,g] = mean(subcomp2012$var_ib[which(subcomp2011$situation == "exit_next")])
table[7,g] = mean(subcomp2012$var_ech[which(subcomp2011$situation == "exit_oth")])
table[8,g] = mean(subcomp2012$var_ib[which(subcomp2011$situation == "exit_oth")])
}

colnames(table) = c("Tous", "TTH1", "TTH2","TTH3", "TTH4")
rownames(table) = c("Ecart d'echelon moyen total", "Ecart d'ib moyen total",
                        "Ecart d'echelon moyen no exit","Ecart d'ib moyen no exit",
                        "Ecart d'echelon moyen exit next","Ecart d'ib moyen exit next",
                        "Ecart d'echelon moyen exit oth","Ecart d'ib moyen exit oth")

print(xtable(table,nrow = nrow(table), align = "lccccc",
             ncol=ncol(table_all)+1, byrow=T, digits = 2),
      sanitize.text.function=identity,size="\\footnotesize",
      only.contents=T, include.colnames = T,
      file = paste0(fig_path,"diff_ech_ib_sim.tex"))



checkTTH3 = comp_data[which(comp_data$c_cir_2011 == "TTH2"),]
table(comp_data$ech_sim[which(comp_data$annee == 2012)], comp_data$ech_obs[which(comp_data$annee == 2011)])
table(comp_data$ech_obs[which(comp_data$annee == 2012)], comp_data$ech_obs[which(comp_data$annee == 2011)])



comp_data = output_global[which(output_global$annee <= 2014),]
list_ok = comp_data$ident[which(comp_data$annee == 2011 & comp_data$situation ==comp_data$situation_BG_1 & comp_data$grade ==comp_data$grade_BG_1)]
comp_data = comp_data[which(is.element(comp_data$ident, list_ok)),]
comp_data$ech_obs = comp_data$echelon
comp_data$ech_sim = comp_data$echelon_BG_1
comp_data$var_ech = comp_data$ech_obs - comp_data$ech_sim
comp_data$ib_obs = comp_data$ib
comp_data$ib_sim = comp_data$ib_BG_1
comp_data$var_ib = comp_data$ib_obs - comp_data$ib_sim

comp2011 = comp_data[comp_data$annee == 2011,]
comp2012 = comp_data[comp_data$annee == 2012,]

table = matrix(ncol = 5, nrow = 8)

list_grade =  c("All", "TTH1", "TTH2", "TTH3", "TTH4")
for (g in 1:length(list_grade))
{
  if (list_grade[g] == "All")
  {
    subcomp2011 = comp2011
    subcomp2012 = comp2012
  }
  if (list_grade[g] != "All")
  {
    subcomp2011 = comp2011[which(comp2011$grade == list_grade[g]),]
    subcomp2012 = comp2012[which(comp2011$grade == list_grade[g]),]
  }
  table[1,g] = median(subcomp2012$var_ech)
  table[2,g] = median(subcomp2012$var_ib)
  table[3,g] = median(subcomp2012$var_ech[which(subcomp2011$situation == "no_exit")])
  table[4,g] = median(subcomp2012$var_ib[which(subcomp2011$situation == "no_exit")])
  table[5,g] = median(subcomp2012$var_ech[which(subcomp2011$situation == "exit_next")])
  table[6,g] = median(subcomp2012$var_ib[which(subcomp2011$situation == "exit_next")])
  table[7,g] = median(subcomp2012$var_ech[which(subcomp2011$situation == "exit_oth")])
  table[8,g] = median(subcomp2012$var_ib[which(subcomp2011$situation == "exit_oth")])
}

colnames(table) = c("Tous", "TTH1", "TTH2","TTH3", "TTH4")
rownames(table) = c("Ecart d'echelon moyen total", "Ecart d'ib moyen total",
                    "Ecart d'echelon moyen no exit","Ecart d'ib moyen no exit",
                    "Ecart d'echelon moyen exit next","Ecart d'ib moyen exit next",
                    "Ecart d'echelon moyen exit oth","Ecart d'ib moyen exit oth")

print(xtable(table,nrow = nrow(table), align = "lccccc",
             ncol=ncol(table_all)+1, byrow=T, digits = 2),
      sanitize.text.function=identity,size="\\footnotesize",
      only.contents=T, include.colnames = T,
      file = paste0(fig_path,"diff_ech_ib_sim.tex"))


