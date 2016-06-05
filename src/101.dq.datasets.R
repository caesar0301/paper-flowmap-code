library(movr)
library(data.table)

senegal.mov <- "data/scl_fine_p06"
senegal.bs <- "data/senegal_site_lonlat.csv"
hangzhou.mov <- "data/hcl_mesos0822"
hangzhou.bs <- "data/hcl_mesos0822_bm"
campus.sessions <- "data/session.sample"

## Senegal
mov <- fread(senegal.mov, sep=",", header=FALSE)
colnames(mov) <- c("uid", "time", "site_id")
bsmap <- fread(senegal.bs, sep=",", header=TRUE)
mov <- mov %>% left_join(bsmap, by=c("site_id"="site_id"))

#people occurrence
po <- people.occurrence(mov$uid, mov$lon, mov$lat)
pc <- point.coverage(mov$lon, mov$lat)
dq1 <- mov %>% group_by(uid) %>% do({
  stc <- stcoords(data.frame(.$lon, .$lat, .$time))
  dq.point(stc, po, pc)
})
dq2 <- dq1 %>% group_by(uid) %>% do(dq.traj2(.))
saveRDS(dq1, "senegal.dq.point.rds")
saveRDS(dq2, "senegal.dq.traj.rds")

## Hangzhou
mov <- fread(hangzhou.mov, sep=",", header=FALSE)
colnames(mov) <- c("uid", "time", "bid")
bsmap <- fread(hangzhou.bs, sep=",", header=FALSE)
colnames(bsmap) <- c("bid", "lacid", "lon", "lat")
mov <- mov %>% left_join(bsmap, by=c("bid"="bid"))
po <- people.occurrence(mov$uid, mov$lon, mov$lat)
pc <- point.coverage(mov$lon, mov$lat)
dq1 <- mov %>% group_by(uid) %>% do({
  stc <- stcoords(data.frame(.$lon, .$lat, .$time))
  dq.point(stc, po, pc)
})
dq2 <- dq1 %>% group_by(uid) %>% do(dq.traj2(.))
saveRDS(dq1, "hz.dq.point.rds")
saveRDS(dq2, "hz.dq.traj.rds")

## SJTU
sessions <- read.csv(campus.sessions, sep=",", header=F, stringsAsFactors=F)
colnames(sessions) <- c('uid', 'stime', 'etime', 'y', 'x')
sessions$stime <- sessions$stime / 1000
sessions$etime <- sessions$etime / 1000
sessions$x <- as.numeric(sessions$x)
sessions$y <- as.numeric(sessions$y)
sessions <- na.omit(sessions)

po <- people.occurrence(sessions$uid, sessions$x, sessions$y)
pc <- point.coverage(sessions$x, sessions$y)
dq1 <- sessions %>% group_by(uid) %>% do({
  if(nrow(.) > 1) dq.point2(., po, pc )
  else data.frame()
})
dq2 <- dq1 %>% group_by(uid) %>% do(dq.traj2(.))
saveRDS(dq1, "sjtu.dq.point.rds")
saveRDS(dq2, "sjtu.dq.traj.rds")
