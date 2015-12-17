## Hangzhou
library(plyr)
library(dplyr)
library(deldir)
library(magicaxis)
library(movr)
library(rgl)

filter <- dplyr::filter

mov <- fread("data/hcl_mesos7d", sep=",", head=F)
setnames(mov, c("uid", "time", "bid"))
mov <- mov %>% as.data.frame %>% filter(uid <= 1000)

bm <- fread("data/hcl_mesos7d_bm", sep=",", head=F, colClasses=c("integer", "character", "numeric", "numeric"))
setnames(bm, c("bid", "bs", "lon", "lat"))
bm <- bm %>% filter(lon >= 120.0 & lon <= 120.5)

# calculate relative coordinates in KM
minlat <- min(bm$lat)
minlon <- min(bm$lon)
relxy <- function(lat, lon) {
  y = gcd(c(lat, minlon), c(minlat, minlon))
  x = gcd(c(minlat, lon), c(minlat, minlon))
  c(x, y)
}
bm <- ddply(bm, c("bid"), function(r) {
  r$x <- gcd(c(minlat, minlon), c(r$lat, minlon))
  r$y <- gcd(c(minlat, minlon), c(minlat, r$lon))
  r
})

# merge bm into mov data
mov2 <- mov %>% as.data.frame %>% left_join(bm, by=c("bid"="bid"))

users <- subset(movement, id %in% c(23, 20)) %>%
  mutate(time = time/86400 - min(time/86400)) %>%
  dplyr::filter(time <= 30)

movr::draw_mobility3d(users$lon, users$lat, users$time,
           group_by=users$id, col=c('royalblue', 'orangered'))
rgl.postscript("figures/mobility3d.pdf", fmt="pdf")
rgl.close()