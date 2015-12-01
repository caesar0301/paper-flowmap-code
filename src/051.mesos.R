library(dplyr)

################################################
#  Mesos clustering
################################################

SAMPLE = 400

for ( C in rev(seq(2, 20))) {

  dat <- read.csv(paste('data/mesos0825_s0dot2/',C,'.txt',sep=''), sep=',', head=F)
  colnames(dat) <- c('u1', 'u2', 'dist')
  
  # Sample users to reduce running time
  uuer <- unique(dat$u1)
  print(length(uuer))
  if (length(uuer) > SAMPLE) {
    suer <- sample(unique(dat$u1), SAMPLE, replace=F)
    dat2 <- dat %>% dplyr::filter(u1 %in% suer, u2 %in% suer)
  } else {
    dat2 <- dat
  }
  
  # 3column data frame to matrix.
  # Available functions: reshape2::dcast, plyr::daply, tidyr::spread,
  # reshape, reshape2::acast, xtabs etc.
  dm <- dat2[!duplicated(dat2[,c('u1','u2')]),] %>% tidyr::spread(u2, dist)
  dm <- as.matrix(dm[1:nrow(dm),2:ncol(dm)])
  
  # Replace NA with distance 1
  dm[which(is.na(dm), arr.ind=TRUE)] <- 1
  
  clust <- hclust(as.dist(dm), method='ward.D2')
  k = 4
  ck <- cutree(clust, k = k)
  ord <- order(ck)
  
  # Save cluster lables for each user
#   for ( j in seq(k)) {
#     selector <- ck==j
#     dmj <- dm[selector,selector]
#     colnames(dmj) <- colnames(dm)[selector]
#     rownames(dmj) <- colnames(dm)[selector]
#     write.table(dmj, paste('data/mesos0825_s0dot2/mesos0825_s0dot2_c',C,'_kn',j,sep=''),
#                 sep=',', row.names=F, col.names=T,quote=F)
#   }

  # Dendrogram
  pdf(paste('figures/mesos0825_s0.2/mesos0825_s0.2_c',C,'_dendrogram.pdf',sep=''), width=7, height=6.2)
  par(mar=c(3,3,1,1), mgp=c(1.5,0.5,0), cex.lab=1.5)
  plot(as.dendrogram(clust), leaflab="none", xlab="Mobility Graph", ylab="Cophenetic distance")

  pal.1 <- colorRampPalette(c("blue", "cyan", "yellow", "red"), bias=0.5)

  # Dissimilarity matrix (inset)
  library(TeachingDemos)
  subplot(image(as.matrix(dm)[ord, ord], col=pal.1(10)), 
    x=grconvertX(c(0.55,0.95), from='npc'),
    y=grconvertY(c(0.55,0.95), from='npc'),
    type='fig', pars=list( mar=c(1.5,1.5,0,0)+0.1) )
  dev.off()
  
  # Standalone
  pdf(paste('figures/mesos0825_s0.2/mesos0825_s0.2_c',C,'_k',k,'_distmat.pdf',sep=''), width=7, height=6.2)
  par(mar=c(3.5,3.5,1,1), mgp=c(2,0.5,0), cex.lab=1.5)
  image(as.matrix(dm)[ord, ord], xlab='Mobility Graph', ylab='Mobility Graph',col=pal.1(10))  
  dev.off()

}


################################################
#  Clusters in one plot
################################################

SAMPLE = 300

nlocdist <- read.csv('data/hcl_mesos0825_ndgr', sep=',', head=T)
hi <- hist(nlocdist$nloc, breaks=max(nlocdist$nloc))
dens <- hi$density

pdf(paste('figures/mesos0825_s0.2/mesos0825_s0.2_distmat.pdf',sep=''), width=8, height=9)
par(mfrow=c(3,3), mar=c(3,1,1,1), mgp=c(1,0.5,0), cex.lab=1.5)

for ( C in seq(2, 10)) {
  
  dat <- read.csv(paste('data/mesos0825_s0dot2/',C,'.txt',sep=''), sep=',', head=F)
  colnames(dat) <- c('u1', 'u2', 'dist')
  
  # Sample users to reduce running time
  uuer <- unique(dat$u1)
  print(length(uuer))
  if (length(uuer) > SAMPLE) {
    suer <- sample(unique(dat$u1), SAMPLE, replace=F)
    dat2 <- dat %>% dplyr::filter(u1 %in% suer, u2 %in% suer)
  } else {
    dat2 <- dat
  }
  
  # 3column data frame to matrix.
  # Available functions: reshape2::dcast, plyr::daply, tidyr::spread,
  # reshape, reshape2::acast, xtabs etc.
  dm <- dat2[!duplicated(dat2[,c('u1','u2')]),] %>% tidyr::spread(u2, dist)
  dm <- as.matrix(dm[1:nrow(dm),2:ncol(dm)])
  
  # Replace NA with distance 1
  dm[which(is.na(dm), arr.ind=TRUE)] <- 1
  
  clust <- hclust(as.dist(dm), method='ward.D2')
  k = 4
  ck <- cutree(clust, k = k)
  ord <- order(ck)

  pal.1 <- colorRampPalette(c("blue", "cyan", "yellow", "red"), bias=0.5)
  image(as.matrix(dm)[ord, ord], axes=F ,col=pal.1(10),
        xlab=paste('C=', C, ', p=', format(dens[C-1]*100, digits=2), '%', sep=''))
}

dev.off()


################################################
#  Self similarity vs. cluster distance
################################################
library(magicaxis)

dat <- read.csv('data/mesos0825_s0dot2/mesos0825_s0dot2_trd', head=T, sep=',')
magplot(log(dat$dist), dat$selfdist, pch=16, col=colors()[222])
abline(0.96, 0.37)


dat_r <- dat %>% dplyr::filter(dist > 0.6 & selfdist < 1 & selfdist > 0.2)
x <- dat_r$dist
y <- dat_r$selfdist
lm.out <- lm(log(y) ~ log(x))
cc <- coef(lm.out)
curve(x^cc[2] * exp(cc[1]), add=T, lwd=2, col='orangered', xlim=c(0.5, 1))
text(0.8, 0.25, substitute(paste(Y, ' ~ ', a * x, b, sep=''),
                           list(a = format(cc[2], digits=3),
                                b =format(cc[1], digits=3))))

dat_r <- dat %>% dplyr::filter(dist < 0.2 & selfdist < 1 & selfdist > 0.01)
magplot(dat$dist, dat$selfdist, pch=16, col=colors()[222])
x <- dat_r$dist
y <- dat_r$selfdist
lm.out <- lm(log(y) ~ log(x))
cc <- coef(lm.out)
curve(x^cc[2] * exp(cc[1]), add=T, lwd=2, col='orangered', xlim=c(0.5, 1))
text(0.8, 0.25, substitute(paste(Y, ' ~ ', a * x, b, sep=''),
                           list(a = format(cc[2], digits=3),
                                b =format(cc[1], digits=3))))