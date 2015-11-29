library(dplyr)

################################################
#  Mesos clustering
################################################

SAMPLE = 400

for ( C in rev(seq(2, 15))) {
  
  dat <- read.csv(paste('data/mesos0822_s0dot2/',C,'.txt',sep=''), sep=',', head=F)
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
  dm <- dat2 %>% tidyr::spread(u2, dist)
  dm <- as.matrix(dm[1:nrow(dm),2:ncol(dm)])
  
  # Replace NA with row means
  i <- which(is.na(dm), arr.ind=TRUE)
  dm[i] <- rowMeans(dm, na.rm=TRUE)[i[,1]]
  
  clust <- hclust(as.dist(dm), method='ward.D2')
  k = 3
  ck <- cutree(clust, k = k)
  ord <- order(ck)
  
  # Save cluster lables for each user
#   for ( j in seq(k)) {
#     selector <- ck==j
#     dmj <- dm[selector,selector]
#     colnames(dmj) <- colnames(dm)[selector]
#     rownames(dmj) <- colnames(dm)[selector]
#     write.table(dmj, paste('data/mesos0822_s0dot2/mesos0822_s0dot2_c',C,'_kn',j,sep=''),
#                 sep=',', row.names=F, col.names=T,quote=F)
#   }

  # Dendrogram
  pdf(paste('figures/mesos0822_s0.2_c',C,'_dendrogram.pdf',sep=''), width=7, height=6.2)
  par(mar=c(3,3,1,1), mgp=c(1.5,0.5,0), cex.lab=1.5)
  plot(as.dendrogram(clust), leaflab="none", xlab="Mobility Graph", ylab="Cophenetic distance")

  # Dissimilarity matrix (inset)
  library(TeachingDemos)
  subplot(image(as.matrix(dm)[ord, ord]), 
    x=grconvertX(c(0.55,0.95), from='npc'),
    y=grconvertY(c(0.55,0.95), from='npc'),
    type='fig', pars=list( mar=c(1.5,1.5,0,0)+0.1) )
  dev.off()
  
  # Standalone
  pdf(paste('figures/mesos0822_s0.2_c',C,'_k',k,'_distmat.pdf',sep=''), width=7, height=6.2)
  par(mar=c(3.5,3.5,1,1), mgp=c(2,0.5,0), cex.lab=1.5)
  image(as.matrix(dm)[ord, ord], xlab='Mobility Graph', ylab='Mobility Graph')  
  dev.off()

}