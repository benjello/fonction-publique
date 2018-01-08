
################################################### Descriptive statistics ##########################################################

# Descriptive statistiscs on the population of interest 
# 0. Initalisation: load and clean data
# I.   Sample description
# II.  Effect of change grade conditions
# III. Effect of change echelon



##### 0. Iniatialisation #####

source(paste0(wd, "0_Outils_CNRACL.R"))
datasets = load_and_clean(data_path, "/filter/data_ATT_2011_filtered_after_duration_var_added_new.csv")
data_max = datasets[[1]]
data_min = datasets[[2]]

data_stat_min = data_min[which(data_min$left_censored == F & data_min$annee <= 2014),]
data_stat_max = data_max[which(data_max$left_censored == F & data_max$annee <= 2014),]
data_stat = data_stat_max
datai     =  data_min[which(data_min$annee == 2011),]



##### I. Sample description ##### 

## I.1 Sample  ####
table_count <- matrix(ncol = 5, nrow = 2)
table_count[1,1] <- length(unique(data_id$ident))
table_count[2,1] <- 100
table_count[1,2:5] <- format(round(as.data.frame(table(data_id$c_cir_2011))[1:4,2]))
table_count[2, 2:5] <- format(round(as.data.frame(table(data_id$c_cir_2011))[1:4,2]/length(unique(data_id$ident))*100,1),1)
colnames(table_count) = c("All", "TTH1","TTH2", "TTH3", "TTH4")
rownames(table_count) = c('\\Number of agents', "\\% share of ATT population")

print(xtable(table_count,align="lccccc",nrow = nrow(table), ncol=ncol(table_censoring)+1, byrow=T, digits = 3),
      sanitize.text.function=identity,size="\\footnotesize", 
      only.contents=F, include.colnames = T)

data <- read.csv(paste0("M:/CNRACL/output/clean_data_finalisation", "/data_ATT_2002_2015_2.csv"))
data_id_bis <- data[!duplicated(data[,"ident"]),]
table_count_grade_next = matrix(ncol = 6, nrow = 2)
table_count_grade_next[1,1] = length(unique(data_id_bis$ident))
table_count_grade_next[2,1] = 100
table_count_grade_next[1,2:6] = format(round(as.data.frame(table(data_id_bis$grade_bef))[1:5,2]))
table_count_grade_next[2, 2:6] = format(round(as.data.frame(table(data_id_bis$grade_bef))[1:5,2]/length(unique(data_id_bis$ident))*100,1),1)
colnames(table_count_grade_next) = c("All", "missing", "other", "TTH1","TTH2", "TTH3")
rownames(table_count_grade_next) = c('\\Number of agents', "\\% share of ATT population")

data_1st_y <- data[which(data$annee == data$last_y_in_grade_bef),]
data_1st_y_autre <- data_1st_y[which(data_1st_y$c_cir == "autre"),]
data_1st_y_autre_ib_null <- data_1st_y[which(data_1st_y$ib == 0),]
print(dim(data_1st_y_autre_ib_null))

data_last_y <- data[which(data$annee == data$first_y_in_next_grade),]

print(xtable(table_count_grade_next,align="lcccccc",nrow = nrow(table), ncol=ncol(table_count_grade_next)+1, byrow=T, digits = 3),
      sanitize.text.function=identity,size="\\footnotesize", 
      only.contents=F, include.colnames = T)

table_count_grade_next = matrix(ncol = 6, nrow = 2)
table_count_grade_next[1,1] = length(unique(data$ident))
table_count_grade_next[2,1] = 100
table_count_grade_next[1,2:6] = format(round(as.data.frame(table(data$grade_bef))[1:5,2]))
table_count_grade_next[2, 2:6] = format(round(as.data.frame(table(data$grade_bef))[1:5,2]/length(unique(data$ident))*100,1),1)
colnames(table_count_grade_next) = c("All", "missing", "other", "TTH1","TTH2", "TTH3")
rownames(table_count_grade_next) = c('\\Number of agents', "\\% share of ATT population")

print(xtable(table_count_grade_next,align="lcccccc",nrow = nrow(table), ncol=ncol(table_count_grade_next)+1, byrow=T, digits = 3),
      sanitize.text.function=identity,size="\\footnotesize", 
      only.contents=F, include.colnames = T)

## I.2 Censoring ####

data_id$right = as.numeric(data_id$right_censored)
data_id$left = as.numeric(data_id$left_censored)

mean_right <- aggregate(data_id$right, by = list(data_id$c_cir_2011), FUN=mean)    
mean_left  <- aggregate(data_id$left,  by = list(data_id$c_cir_2011), FUN=mean)    

table_censoring = matrix(ncol = 5, nrow = 2)
table_censoring[1,1] = mean(data_id$right)
table_censoring[1,2:5] = mean_right$x
table_censoring[2,1] = mean(data_id$left)
table_censoring[2,2:5] = mean_left$x

colnames(table_censoring) = c("All", "TTH1","TTH2", "TTH3", "TTH4")
rownames(table_censoring) = c('\\% right-censored', "\\% left-censored")

print(xtable(table_censoring,align="lccccc",nrow = nrow(table), ncol=ncol(table_censoring)+1, byrow=T, digits = 3),
      sanitize.text.function=identity,size="\\footnotesize", 
      only.contents=F, include.colnames = T)



## I.3 Stats on transitions ####

compute_transitions_next <- function(data, grade)
{
  data = data[which(data$c_cir_2011 == grade & data$annee == 2011),]
  table_exit = numeric(12)
  # % in each possible next_grade_situation
  table_exit[1] = round(length(which(data$next_grade_situation == "no_exit"))*100/length(data$next_grade_situation),2)
  table_exit[2] = round(length(which(data$next_grade_situation == "exit_next"))*100/length(data$next_grade_situation),2)
  table_exit[3] = round(length(which(data$next_grade_situation == "exit_oth"))*100/length(data$next_grade_situation),2)
  # From other known neg
  data_exit_oth = data[which(data$next_grade_situation == "exit_oth"), ]
  t = as.data.frame(table(data_exit_oth$grade_next)*100/length(data_exit_oth$grade_next))
  t = t[order(-t$Freq),]
  for (n in 1:4){
    table_exit[3+2*n-1] = toString(t[n,1])
    table_exit[3+2*n] = round(t[n,2],2)
  }
  table_exit[12] = length(which(t$Freq >0))
  return(table_exit)
}


table1 = compute_transitions_next(data_stat, "TTH1")
table2 = compute_transitions_next(data_stat, "TTH2")
table3 = compute_transitions_next(data_stat, "TTH3")
table4 = compute_transitions_next(data_stat, grade = "TTH4")

table = cbind(table1, table2, table3, table4)

colnames(table) <-  c("TTH1", "TTH2", "TTH3", "TTH4")
rownames(table) <-  c("\\% no exit", "\\% exit next", "\\% exit oth",
                      "\\hfill 1st oth grade ", "\\hfill  \\% 1st oth", 
                      "\\hfill 2nd oth grade ", "\\hfill  \\% 2nd oth", 
                      "\\hfill 3rd oth grade ", "\\hfill  \\% 3rd oth", 
                      "\\hfill 4th oth grade ", "\\hfill  \\% 4th oth", 
                      "Nb oth grades")

as.numeric(table[c(1,2,3,5,7,9,11), ]) <- as.numeric(table[c(1,2,3,5,7,9,11), ])

print(xtable(table),
      sanitize.text.function=identity,size="\\footnotesize")

##  Grade de destination quand exit oht par grade et anne ####

compute_transitions_oth <- function(data, grade, years)
{
  data = data[which(data$c_cir_2011 == grade & is.element(data$annee, years)),]
  data_exit_oth = data[which(data$next_year == "exit_oth"), ]
  table_exit = numeric(10)
  # % exit oth
  table_exit[1] = round(length(data_exit_oth$ident)*100/length(data$ident),2)
  t = as.data.frame(table(data_exit_oth$next_grade)*100/length(data_exit_oth$next_grade))
  t = t[order(-t$Freq),]
  for (n in 1:4){
    table_exit[1+2*n-1] = toString(t[n,1])
    table_exit[1+2*n] = round(t[n,2],2)
  }
  table_exit[10] = length(which(t$Freq >0))
  return(table_exit)
}

for (y in 2011:2014)
{  
  for (g in c("TTH1", "TTH2", "TTH3", "TTH4"))
  {
    subtable = compute_transitions_oth(data_min, grade = g, years = y)
    if (g == "TTH1"){tabley = subtable}
    else{ tabley = cbind(tabley, subtable)  }
  }
  print(tabley)
  if (y == 2011){table = tabley}
  else{ table = rbind(table, tabley)  }  
}


colnames(table) <-  c("TTH1", "TTH2", "TTH3", "TTH4")
rownames(table) <-  c("\\% no exit", "\\% exit next", "\\% exit oth",
                      "\\hfill 1st oth grade ", "\\hfill  \\% 1st oth", 
                      "\\hfill 2nd oth grade ", "\\hfill  \\% 2nd oth", 
                      "\\hfill 3rd oth grade ", "\\hfill  \\% 3rd oth", 
                      "\\hfill 4th oth grade ", "\\hfill  \\% 4th oth", 
                      "Nb oth grades")

as.numeric(table[c(1,2,3,5,7,9,11), ]) <- as.numeric(table[c(1,2,3,5,7,9,11), ])

print(xtable(table),
      sanitize.text.function=identity,size="\\footnotesize")





####### II. Hazard and surival analysis #######


# II.1 Exit analysis ####


data = extract_exit(data_stat, "next_year")

list_TTH1 = which(datai$c_cir_2011 == "TTH1")
list_TTH2 = which(datai$c_cir_2011 == "TTH2")
list_TTH3 = which(datai$c_cir_2011 == "TTH3")
list_TTH4 = which(datai$c_cir_2011 == "TTH4")


types = c(1, 1, 2)
routes = c("all", "exit_next", "exit_oth")
colors = c("black", "darkcyan", "darkcyan")
### All
list = 1:length(data$ident)
haz = matrix(ncol= length(2011:2014), nrow = 3)
for (t in 1:length(routes)){haz[t,] = compute_hazard(data, list, type = routes[t])}
plot_hazards(haz, colors, types, title = "Tous")

### TTH1
list = list_TTH1
haz = matrix(ncol= length(2011:2014), nrow = 3)
for (t in 1:length(routes)){haz[t,] = compute_hazard(data, list, type = routes[t])}
plot_hazards(haz, colors, types, title = "TTH1")
### TTH2
list = list_TTH2
haz = matrix(ncol= length(2011:2014), nrow = 3)
for (t in 1:length(routes)){haz[t,] = compute_hazard(data, list, type = routes[t])}
plot_hazards(haz, colors, types, title = "TTH2")
### TTH3
list = list_TTH3
haz = matrix(ncol= length(2011:2014), nrow = 3)
for (t in 1:length(routes)){haz[t,] = compute_hazard(data, list, type = routes[t])}
plot_hazards(haz, colors, types, title = "TTH3")
### TTH4
list = list_TTH4
haz = matrix(ncol= length(2011:2014), nrow = 3)
for (t in 1:length(routes)){haz[t,] = compute_hazard(data, list, type = routes[t])}
plot_hazards(haz, colors, types, title = "TTH4")


# II.2 Effect of institutional threshold ####

#TTH1
subdata = data_stat
subdata = subdata[which(subdata$left_censored == F & subdata$c_cir_2011 == "TTH1"),]


pdf(paste0(fig_path,"hazard_by_duree_TTH1.pdf"))
hazard_by_duree(data = subdata)
abline(v = 3, lwd = 3)
abline(v = 10, lwd = 3)
dev.off()

pdf(paste0(fig_path,"hazard_by_ech_TTH1.pdf"))
hazard_by_ech(data = subdata)
abline(v = 4, lwd = 3)
abline(v = 7, lwd = 3)
dev.off()

# Variantes duree aff
subdata2 = subdata
subdata2$time = subdata2$annee - subdata2$an_aff +1
pdf(paste0(fig_path,"hazard_by_duree_TTH1_bis.pdf"))
hazard_by_duree(data = subdata2)
abline(v = 3, lwd = 3)
abline(v = 10, lwd = 3)
dev.off()

# Double condition
pdf(paste0(fig_path,"hazard_by_duree_TTH1_cond.pdf"))
hazard_by_duree(data = subdata2[which(subdata2$echelon >= 4),])
abline(v = 3, lwd = 3)
dev.off()

hazard_by_duree(data = subdata2[which(subdata2$echelon >= 4),], type_exit = "in_corps")
abline(v = 3, lwd = 3)
hazard_by_ech(data = subdata2[which(subdata2$time >= 3),], type_exit = "in_corps")
abline(v = 4, lwd = 3)
hazard_by_duree(data = subdata2[which(subdata2$echelon >= 4),], type_exit = "out_corps")
abline(v = 3, lwd = 3)
hazard_by_ech(data = subdata2[which(subdata2$time >= 3),], type_exit = "out_corps")
abline(v = 4, lwd = 3)


pdf(paste0(fig_path,"hazard_by_ech_TTH1_cond.pdf"))
hazard_by_ech(data = subdata2[which(subdata2$time >= 10),])
abline(v = 7, lwd = 3)
dev.off()


# TTH2
subdata = data_stat
subdata = subdata[which(subdata$left_censored == F & subdata$c_cir_2011 == "TTH2" & subdata$annee >= 2011),]
hazard_by_duree(data = subdata)
hazard_by_ech(data = subdata)

pdf(paste0(fig_path,"hazard_by_duree_TTH2.pdf"))
hazard_by_duree(data = subdata)
abline(v = 6, lwd = 3)
dev.off()

pdf(paste0(fig_path,"hazard_by_ech_TTH2.pdf"))
hazard_by_ech(data = subdata)
abline(v = 5, lwd = 3)
dev.off()


# Variantes duree aff
subdata2 = subdata[which(subdata$left_censored == F & subdata$c_cir_2011 == "TTH2"),]
subdata2$time = subdata2$annee - subdata2$an_aff +1
pdf(paste0(fig_path,"hazard_by_duree_TTH2_bis.pdf"))
hazard_by_duree(data = subdata2, corps = T)
abline(v = 6, lwd = 3)
dev.off()
pdf(paste0(fig_path,"hazard_by_duree_TTH2_bis_exit_next.pdf"))
hazard_by_duree(data = subdata2, corps = T, type_exit = "in_corps")
abline(v = 6, lwd = 3)
dev.off()

# Double condition
pdf(paste0(fig_path,"hazard_by_duree_TTH2_cond.pdf"))
hazard_by_duree(data = subdata2[which(subdata2$echelon >= 5),])
abline(v = 6, lwd = 3)
dev.off()

hazard_by_duree(data = subdata2[which(subdata2$echelon >= 7),], type_exit = "in_corps")
abline(v = 6, lwd = 3)
hazard_by_duree(data = subdata2[which(subdata2$echelon >= 7),], type_exit = "out_corps")
abline(v = 6, lwd = 3)

pdf(paste0(fig_path,"hazard_by_ech_TTH2_cond.pdf"))
hazard_by_ech(data = subdata2[which(subdata2$time >= 6),])
abline(v = 5, lwd = 3)
dev.off()

hazard_by_ech(data = subdata2[which(subdata2$time >= 6),], type_exit = "in_corps")
abline(v = 5, lwd = 3)
hazard_by_ech(data = subdata2[which(subdata2$time >= 6),], type_exit = "out_corps")
abline(v = 5, lwd = 3)


# TTH3 
subdata = data_stat_min
subdata = subdata[which(subdata$left_censored == F & subdata$c_cir_2011 == "TTH3" & subdata$annee <= 2014& subdata$annee >= 2011),]
hazard_by_duree(data = subdata)
abline(v = 5, lwd = 3)
hazard_by_duree(data = subdata, type_exit = "in_corps")
abline(v = 5, lwd = 3)
hazard_by_duree(data = subdata, type_exit = "out_corps")
abline(v = 5, lwd = 3)
hazard_by_ech(data = subdata)
abline(v = 6, lwd = 3)
hazard_by_ech(data = subdata, type_exit = "in_corps")
abline(v = 6, lwd = 3)
hazard_by_ech(data = subdata, type_exit = "out_corps")
abline(v = 6, lwd = 3)

pdf(paste0(fig_path,"hazard_by_duree_TTH3.pdf"))
hazard_by_duree(data = subdata)
abline(v = 5, lwd = 3)
dev.off()

pdf(paste0(fig_path,"hazard_by_ech_TTH3.pdf"))
hazard_by_ech(data = subdata)
abline(v = 6, lwd = 3)
dev.off()


# Double conditions
pdf(paste0(fig_path,"hazard_by_duree_TTH3_cond.pdf"))
hazard_by_duree(data = subdata[which(subdata$echelon >= 6),])
abline(v = 5, lwd = 3)
dev.off()

pdf(paste0(fig_path,"hazard_by_ech_TTH3_cond.pdf"))
hazard_by_ech(data = subdata[which(subdata$time >= 5),])
abline(v = 6, lwd = 3)
dev.off()


# TTH4
subdata = data_stat
subdata = subdata[which(subdata$left_censored == F & subdata$c_cir_2011 == "TTH4"),]
hazard_by_duree(data = subdata)
hazard_by_ech(data = subdata)


pdf(paste0(fig_path,"hazard_by_duree_TTH4.pdf"))
hazard_by_duree(data = subdata)
dev.off()

pdf(paste0(fig_path,"hazard_by_ech_TTH4.pdf"))
hazard_by_ech(data = subdata)
dev.off()




####### III. Duration spent in echelon #######


filename = paste0(data_path,"clean_data_finalisation/data_ATT_2002_2015_with_filter_on_etat_at_exit_and_change_to_filter_on_etat_quarterly.csv")
data_ech = read.csv(filename)  

list_id = unique(data_stat$ident)
data_ech = data_ech[which(is.element(data_ech$ident, list_id)), ]
data_ech = data_ech[which(data_ech$annee < data_ech$last_y_observed_in_grade), ]

# Count echelon transition

data_ech$bef_ech <-ave(data_ech$echelon, data_ech$ident, FUN=shiftm1)
data_ech$change_ech <- ifelse((data_ech$echelon != data_ech$bef_ech & !is.na(data_ech$bef_ech)), 1, 0)
data_ech$change_ech[which(is.na(data_ech$change_ech))] = 1

data_ech$year_change = data_ech$annee*data_ech$change_ech
data_ech$cumsum  <- ave(data_ech$change_ech ,data_ech$ident, FUN=cumsum)
data_ech$tot     <- ave(data_ech$change_ech,data_ech$ident,FUN=sum)

# Drop first and last transition
data = data_ech[-which(data_ech$cumsum == 0 | data_ech$cumsum == data_ech$tot),]
# Keep only first transition 
data_first = data[which(data$cumsum == 1 & data$tot >1 ),]
data_first$a       <- 1
data_first$dur_ech <- ave(data_first$a, data_first$ident ,FUN=sum)
data_first = data_first[!duplicated(data_first$ident),]
# Drop when 
#data_first = data_first[which(data_first$year_change == 2011),]


list_grade = c("TTH1", "TTH2", "TTH3")
for (g in 1:length(list_grade))
{
subdata = data_first[which(data_first$c_cir_2011 == list_grade[g]),]
dur_ech = seq(1:15)
dist_dur_ech = matrix(ncol = length(dur_ech), nrow = 4)
for (t in 1:length(dur_ech))
{
  dist_dur_ech[1,t] = length(which(subdata$dur_ech == dur_ech[t] & subdata$echelon == 1))/length(which(subdata$echelon == 1))
  dist_dur_ech[2,t] = length(which(subdata$dur_ech == dur_ech[t] & subdata$echelon  >= 2 & subdata$echelon <= 3))/length(which(subdata$echelon  >= 2 & subdata$echelon <= 3))
  dist_dur_ech[3,t] = length(which(subdata$dur_ech == dur_ech[t] & subdata$echelon  >= 4 & subdata$echelon <= 6))/length(which(subdata$echelon  >= 4 & subdata$echelon <= 6))  
  dist_dur_ech[4,t] = length(which(subdata$dur_ech == dur_ech[t] & subdata$echelon  >= 7))/length(which(subdata$echelon  >= 7))
}  


cond = c(4, 6, 8, 12)
col1 = c(rep("cadetblue2", 4-1), "cadetblue4", rep("cadetblue2", 15-4))
col2 = c(rep("cadetblue2", 6-1), "cadetblue4", rep("cadetblue2", 15-6))
col3 = c(rep("cadetblue2", 8-1), "cadetblue4", rep("cadetblue2", 15-8))
col4 = c(rep("cadetblue2", 12-1), "cadetblue4", rep("cadetblue2", 15-12))

pdf(paste0(fig_path, list_grade[g],"_dur_ech.pdf"))
if (g == 1)
{  
layout(matrix(c(1,2,3), nrow=1,ncol=3, byrow=TRUE))
labels = c(NA, 6, NA, 12, NA, 18, NA, 24, NA, 30, NA, 36, NA, 42, NA)
par(mar=c(5,4.1,2,0.2))
#barplot(dist_dur_ech[1,],ylab="",xlab="", col = col1, names.arg = labels, main = "Level == 1", font.axis = 2,cex.names = 1.3, cex.axis =  1)
barplot(dist_dur_ech[2,],ylab="",xlab="", col = col2, names.arg = labels, main = "2<= Echelon <=3", font.axis = 2,cex.names = 1.3, cex.axis =  1)
barplot(dist_dur_ech[3,],ylab="",xlab="Duration (in month)", col = col3, names.arg = labels, main = " 4<= Echelon <=6", font.axis = 2,cex.names = 1.3, cex.axis =  1, cex.lab = 1.5)
barplot(dist_dur_ech[4,],ylab="",xlab="", col = col4, names.arg = labels, main = "Echelon >= 7", , font.axis = 2,cex.names = 1.3, cex.axis =  1)
dev.off()
}
if (g > 1)
{
layout(matrix(c(1,2), nrow=1,ncol=2, byrow=TRUE))
labels = c(NA, 6, NA, 12, NA, 18, NA, 24, NA, 30, NA, 36, NA, 42, NA)
par(mar=c(5,4.1,2,0.2))
barplot(dist_dur_ech[3,],ylab="",xlab="Duration (in month)", col = col3, names.arg = labels, main = " 4<= Echelon <=6", font.axis = 2,cex.names = 1.3, cex.axis =  1, cex.lab = 1.5)
barplot(dist_dur_ech[4,],ylab="",xlab="", col = col4, names.arg = labels, main = "Echelon >= 7", , font.axis = 2,cex.names = 1.3, cex.axis =  1)
dev.off()  
}
}


##### CHECK WEIRD INDIVIDUALS #####
list_weird_TTH3 <- unique(data_stat$ident[which(data_stat$c_cir_2011 == "TTH3" & data_stat$time < data_stat$D_choice & data_stat$next_year == "exit_next")])
list = list_weird_TTH3[1:10]
View(data_min[which(is.element(data_min$ident, list)), ])
View(data_max[which(is.element(data_max$ident, list)), ])
