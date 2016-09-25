library(dplyr)
library(magicaxis)
library(stringr)

emp <- read.csv('data/mesos_model_emp_stat', sep='\t', head=F)
colnames(emp) <- c('uid', 'rg', 'totloc', 'totdist', 'trvdist')

mom <- read.csv('data/mesos_model_mom_stat', sep='\t', head=F)
colnames(mom) <- c('uid', 'rg', 'totloc', 'totdist', 'trvdist')

rwm <- read.csv('data/mesos_model_rwm_stat', sep='\t', head=F)
colnames(rwm) <- c('uid', 'rg', 'totloc', 'totdist', 'trvdist')

fem <- read.csv('data/mesos_model_fem', sep='\t', head=F)
colnames(fem) <- c('uid', 'rg', 'totloc', 'totdist', 'trvdist')

###############
## Travelling distance total
###############

emp_dist <- emp$totdist
mom_dist <- mom$totdist
rwm_dist <- rwm$totdist
fem_dist <- fem$totdist

pdf('figures/mesos_model_totdist.pdf', height=4.5, width=6)
par(mar=c(4,4,1,1), mgp=c(1,0.5,0), cex.lab=2)
magplot(density(emp_dist), log='x', xlab='Total Distance (km)', ylab='Probability', xlim=c(1, 200), lwd=2)
lines(density(mom_dist), log='x', col='orangered', lty=6, lwd=2)
lines(density(rwm_dist), log='x', col=colors()[572], lty=4, lwd=2)
lines(density(fem_dist), log='x', col='royalblue',lty=5, lwd=2)
legend(50, 0.03, c('Empirical', 'MOM', 'RWM', 'FEM'), lty=c(1,6,4,5), col=c('black','orangered',colors()[572],'royalblue'), lwd=2)
dev.off()


###############
## Total locations
###############

emp_locs <- emp$totloc
mom_locs <- mom$totloc
rwm_locs <- rwm$totloc
fem_locs <- fem$totloc

pdf('figures/mesos_model_totloc.pdf', height=4.5, width=6)
par(mar=c(4,4,1,1), mgp=c(1,0.5,0), cex.lab=2)
magplot(density(emp_locs), log='x', xlab='Total Locations', ylab='Probability', xlim=c(1, 20), lwd=2)
lines(density(mom_locs), log='x', col='orangered', lty=6, lwd=2)
lines(density(rwm_locs), log='x', col=colors()[572], lty=4, lwd=2)
lines(density(fem_locs), log='x', col='royalblue',lty=5, lwd=2)
legend(8, 0.25, c('Empirical', 'MOM', 'RWM', 'FEM'), lty=c(1,6,4,5), col=c('black','orangered',colors()[572],'royalblue'), lwd=2)
dev.off()

################
## Jump sizes
################

extract_jump_sizes <- function(dat) {
  js <- c()
  trvdist <- dat$trvdist
  for ( i in seq(1, length(trvdist)) ) {
    js <- c(js, as.numeric(str_split(trvdist[i], ',')[[1]]))
  }
  js
}

mom_js <- extract_jump_sizes(mom)
emp_js <- extract_jump_sizes(emp)
rwm_js <- extract_jump_sizes(rwm)
fem_js <- extract_jump_sizes(fem)

pdf('figures/mesos_model_js.pdf', height=4.5, width=6)
par(mar=c(4,4,1,1), mgp=c(1,0.5,0), cex.lab=2)
magplot(density(emp_js), log='x', xlab='Jump size (km)', ylab='Probability', xlim=c(0.01, 20), lwd=2)
lines(density(mom_js), log='x', col='orangered', lty=6, lwd=2)
lines(density(rwm_js), log='x', col=colors()[572], lty=4, lwd=2)
lines(density(fem_js), log='x', col='royalblue',lty=5, lwd=2)
legend(2, 0.5, c('Empirical', 'MOM', 'RWM', 'FEM'), lty=c(1,6,4,5), col=c('black','orangered',colors()[572],'royalblue'), lwd=2)
dev.off()
