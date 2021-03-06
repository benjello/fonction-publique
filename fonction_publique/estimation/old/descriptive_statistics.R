

#### 0. Initialisation ####

rm(list = ls()); gc()

# path
place = "ippS"
if (place == "ippS"){
  data_path = "M:/CNRACL/output/estimations/"
  git_path =  'U:/Projets/CNRACL/fonction-publique/fonction_publique/'
}
if (place == "ippL"){
  data_path = "M:/CNRACL/output/base_AT_clean_2007_2011/"
  git_path =  'C:/Users/l.degalle/CNRACL/fonction-publique/fonction_publique/'
}
if (place == "mac"){
  data_path = "/Users/simonrabate/Desktop/data/CNRACL/output/"
  git_path =  '/Users/simonrabate/Desktop/IPP/CNRACL/fonction_publique/'
}

# Packages
#install.packages("OIsurv");install.packages("rms");install.packages("emuR");install.packages("RColorBrewer");install.packages("RcmdrPlugin");install.packages("pec")
#install.packages("prodlim")
library(OIsurv)
library(rms)
library(emuR)
library(RColorBrewer)
library(RcmdrPlugin.survival)

# Chargement de la base
filename = paste0(data_path,"base_AT_clean_2007.csv")
data_long = read.csv(filename) 

data_long$ind_exit_once = ave(data_long$exit_status, data_long$ident, FUN = max) 
data_long$observed = ifelse(data_long$ind_exit_once == 1, 1, 0)
data_long$time_min = data_long$min_duration_in_grade + data_long$duration_in_grade_from_2011
data_long$time_max = data_long$max_duration_in_grade + data_long$duration_in_grade_from_2011


# Mise au format data 1obs/indiv
data_id = data_long[,c("ident", "c_cir", "generation_group","max_duration_in_grade","min_duration_in_grade", "an_aff",
                       "grade_de_2011", "duration_in_grade_from_2011", 'ambiguity_2007',
                       "observed",  "right_censoring","left_censoring", "time_min", "time_max", "change")]
data_id = data_id[!duplicated(data_id$ident),]


#### I. Censoring ####
detach(data_id)
attach(data_id)
# Count left and right censoring by grade
table(right_censoring)
table(left_censoring)
table(right_censoring[left_censoring  == "False"])/length(right_censoring[left_censoring  == "False"])
table(right_censoring[left_censoring  == "True"])/length(right_censoring[left_censoring  == "True"])
table(right_censoring[ambiguity_2007  == "False"])/length(right_censoring[ambiguity_2007  == "False"])
table(right_censoring[ambiguity_2007  == "True"])/length(right_censoring[ambiguity_2007  == "True"])
table(right_censoring[(!left_censoring)])

table(right_censoring, left_censoring)


# Count left and right censoring by grade
table(right_censoring, grade_de_2011)
table(left_censoring, grade_de_2011)

list0 = which(grade_de_2011 == 'TTH1')
list1 = which(grade_de_2011 == 'TTH1' & left_censoring == "False")
list2 = which(grade_de_2011 == 'TTH1' & left_censoring == "True")
table(right_censoring[list0])/length(list0)
table(right_censoring[list1])/length(list1)
table(right_censoring[list2])/length(list2)


# Right censoring by grade and time spent in 2011. 
table(time_max)


attach(data)

table(cir_2011)
table(cir_2011[ind_left_censoring == 1])
table(cir_2011[ind_left_censoring == 0])

stat = matrix(ncol = 5, nrow = 5)

# Nb observation
stat[1, 1:5] = as.vector(table(cir_2011))
stat[1, 1] = length(cir_2011)
# Parti
stat[2, 1:5] = table(cir_2011[ind_left_censoring == 0])
stat[2, 1]   = length(which(ind_left_censoring == 0))
stat[3, 1:5] = stat[2, 1:5]/stat[1, 1:5]
# Censur�
stat[4, 1:5] = table(cir_2011[ind_left_censoring == 1])
stat[4, 1]   = length(which(ind_left_censoring == 1))
stat[5, 1:5] = stat[4, 1:5]/stat[1, 1:5]


colnames(stat) <- c("Tous","TTH1", "TTH2", "TTH3", "TTH4")
rownames(stat) <- c("Nb d'individus","Nb non censur�s", "Prop non censur�s","Nb d'ind censur�s", "Prop censur�s")
print(xtable(stat,align="lccccc",nrow = nrow(stat), ncol=ncol(stat)+1, byrow=T, digits = 2),
      sanitize.text.function=identity,size="\\footnotesize", 
      only.contents=F, include.colnames = T, hline.after = c(-1,1,3,5))


detach(data_id)



#### I. Annee affilation ####

data_id$max_duration_in_grade2 = 2011 - data_id$an_aff
data_id$time_max2 = data_id$max_duration_in_grade2 + data_id$duration_in_grade_from_2011



distrib_an_aff = function(data)
{
years = seq(2001, 2011, 1)
freq = numeric(length(years))
for (y in 1:length(years)){freq[y] = length(which(data$an_aff == years[y]))/ length(data$an_aff)}  
return(freq)
}  
  
x = seq(2001, 2011, 1)
tth1 = distrib_an_aff(data_id[which(data_id$c_cir_2011 == "TTH1"),])
tth2 = distrib_an_aff(data_id[which(data_id$c_cir_2011 == "TTH2"),])
tth3 = distrib_an_aff(data_id[which(data_id$c_cir_2011 == "TTH3"),])
tth4 = distrib_an_aff(data_id[which(data_id$c_cir_2011 == "TTH4"),])
layout(matrix(c(1,2,3,4), nrow=2, ncol=2, byrow=TRUE), heights=c(3,3))
par(mar=c(3,4,2,0.2))
barplot  (tth1,ylab="Part des effectifs du grade",xlab="Ann�e d'affiliation", main = "TTH1",  
          names.arg=years, col = "darkcyan")
barplot  (tth2,ylab="Part des effectifs du grade",xlab="Ann�e d'affiliation", main = "TTH2",  
          names.arg=years, col = "darkcyan")
barplot  (tth3,ylab="Part des effectifs du grade",xlab="Ann�e d'affiliation", main = "TTH3",  
          names.arg=years, col = "darkcyan")
barplot  (tth4,ylab="Part des effectifs du grade",xlab="Ann�e d'affiliation", main = "TTH4",  
          names.arg=years, col = "darkcyan")


  lines(x,exit_rate_mro[a,]         ,col=n_col[1],lwd=3)
  lines(x,exit_rate_mro_ci_sup[a,]  ,col=n_col[1],lwd=2,lty=2)
  lines(x,exit_rate_mro_ci_inf[a,]  ,col=n_col[1],lwd=2,lty=2)
  lines(x,exit_rate_nomro[a,]       ,col=n_col[2],lwd=3)
  lines(x,exit_rate_nomro_ci_sup[a,],col=n_col[2],lwd=2,lty=2)
  lines(x,exit_rate_nomro_ci_inf[a,],col=n_col[2],lwd=2,lty=2)
  abline(v=2003, lwd=2)
  abline(v=2010, lwd=2)
}




filename = paste0(data_path,"clean_data_finalisation/data_ATT_2002_2015.csv")




table(data_id$right_censoring[which(data_id$grade_de_2011 == "TTH1")], data_id$max_duration_grade2[which(data_id$grade_de_2011 == "TTH1")])


table(an_aff)
table(an_aff[which(grade_de_2011 == "TTH1")])
table(an_aff[which(grade_de_2011 == "TTH1" & right_censoring == "False")])

d





