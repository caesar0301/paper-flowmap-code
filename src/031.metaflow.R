library(plyr)
library(dplyr)
library(movr)
library(deldir)
library(magicaxis)

mov <- readRDS("rdata/hcl.rds") %>% filter(uid <= 5000)
bm <- readRDS("rdata/hcl_bm.rds")
mov$uid <- as.numeric(mov$uid)

tz2offset <- function(tz) {
  timestr = "2000-01-10 12:00:00"
  format = "%Y-%m-%d %H:%M:%S"
  v = as.numeric(strptime(timestr, format, tz="GMT")) - 
    as.numeric(strptime(timestr, format, tz=tz))
  v/3600
}

# calculate relative coordinates in KM
merge.movbs <- function(mov, bm) {
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
  mov %>% left_join(bm, by=c("bid"="bid"))
}

mov <- mov %>% merge.movbs(bm) %>%
  mutate(t = as.POSIXct(time, tz="Asia/Shanghai", origin="1970-01-01"))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# plot voronoi canvas
plot.voronoi <- function(x, y, ...) {
  dd <- deldir(x, y, ...)
  magplot(x, y, pch=21, bg=colors()[500], col="white", ...)
  dirsgs <- dd$dirsgs
  segments(dirsgs$x1, dirsgs$y1, dirsgs$x2, dirsgs$y2, lty=2, lwd=0.8)
}

# plot individual's movment history on 2D plain
user <- mov %>% filter(uid == 1)
ubm <- user %>% transmute(x, y) %>% distinct %>%
  mutate(index = seq.int(length(x)))
plot.voronoi(ubm$x, ubm$y, xlab="Lon", ylab="Lat")
segs = length(user$x) -1
arrows(user$x[1:segs], user$y[1:segs], user$x[2:segs+1], user$y[2:segs+1],
       length=0.1, angle=15)

# plot individual's movement history in different time slots
offset = tz2offset("Asia/Shanghai")
user <- mov %>% filter(uid == 8)
user$slot = seq_distinct((user$time %/% 3600 + offset + 3) %/% 24)
unique_slots = unique(user$slot)
opar <- par()
par(mfrow=c(2,3))
for ( i in unique_slots[3:8]) {
  user_slot <- filter(user, slot == i)
  ubm <- user_slot %>% transmute(x, y) %>% distinct %>%
    mutate(index = seq.int(length(x)))
  plot.voronoi(ubm$x, ubm$y, xlab="Lon", ylab="Lat")
  segs = length(user$x) -1
  arrows(user$x[1:segs], user$y[1:segs], user$x[2:segs+1], user$y[2:segs+1],
         length=0.1, angle=15)
}
par(opar)
