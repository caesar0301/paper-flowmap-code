## Visualize flowmap in an elegant way.
## Xiaming
library(dplyr)
library(movr)
library(geosphere)

#' Visualize flowmap.
#' 
#' Visualize the mobility statistics (flowmap) from data. Each row in the data
#' will generate a line on the map.
#' 
#' @param from_lat, from_lon The latitude/longitude coordinates of departing point for mobile transitions.
#' @param to_lat, to_lon The latitude/longitude coordinates of arriving point for mobile transitions.
#' @param bg The background color for output figure.
#' @param gc.breaks The number of intermediate points (excluding two ends) to draw a great circle path.
#' @param col.pal A color vector used by \code{colorRampPalette}; must be a valid argument to \code{col2rgb}.
#'        Refer to \url{colorbrewer2.org} to derive more palettes.
#' @param col.pal.bias The bias coefficient used by \code{colorRampPalette}. Higher values give more widely
#'        spaced colors at the high end.
#' @param col.pal.grad The number of color grades to diffeciate distance.
#'
draw_flowmap <- function(from_lat, from_lon, to_lat, to_lon, bg="black", gc.breaks=5,
                         col.pal=c("white", "blue", "black"), col.pal.bias=0.3, col.pal.grad=200) {
  ## install.packages("devtools")
  ## devtools::install_github("caesar0301/movr")
  library(movr)
  
  df <- data.frame(from_lat=from_lat, from_lon=from_lon, to_lat=to_lat, to_lon=to_lon)
    
  # add great circle distances
  dist = apply(df, 1, function(x)
    distGeo(x[c('from_lon', 'from_lat')], x[c('to_lon', 'to_lat')]))
  maxdist = max(dist)
  mindist = min(dist)
  df <- df %>% mutate(dist_ord = movr::vbin(log(dist + 0.001), col.pal.grad)) %>%
    mutate(dist_perc=(dist-mindist)/(maxdist - mindist))
  
  x_axis = seq(min(c(df$from_lon, df$to_lon)), max(c(df$from_lon, df$to_lon)), length.out = 100)
  y_axis = seq(min(c(df$from_lat, df$to_lat)), max(c(df$from_lat, df$to_lat)), length.out = 100)
  
  opar <- par()
  par(bg="black")
  plot(x_axis, y_axis, type="n", axes=F, xlab="", ylab="")
  
  pal.1 <- colorRampPalette(col.pal, bias=col.pal.bias)(col.pal.grad)
  
  apply(df, 1, function(x) {
    p1 = as.numeric(c(x['from_lon'], x['from_lat']))
    p2 = as.numeric(c(x['to_lon'], x['to_lat']))
    
    # use geosphere to generate intermediate points of great circles
    cps = gcIntermediate(p1, p2, n=gc.breaks, addStartEnd=T)
    
    # col = scales::alpha('blue', 1-x['dist_perc'])
    col = pal.1[x['dist_ord']] # longest dist takes black color
    
    lines(cps, col=col)
  })
  
  par(opar)
}

#######################
## Senegal
#######################
locmap <- read.csv('data/SITE_ARR_LONLAT.CSV', head=T, sep=',')
dat <- read.csv('data/scl_fine_p06_fm_i24h', head=F, sep=',')
colnames(dat) <- c("interval", "from", "to", "unique", "total")

dat2 <- dat %>% left_join(locmap, by=c('from' = 'site_id')) %>%
  select(-arr_id, from_lon=lon, from_lat=lat) %>%
  left_join(locmap, by=c('to' = 'site_id')) %>%
  select(-arr_id, to_lon=lon, to_lat=lat)

jpeg('figures/scl_fine_p06_fm_i24h.jpg', width=6400, height=4800)
dat3 <- dat2[sample(1:nrow(dat2), 600000, replace=F),]
draw_flowmap(dat3$from_lat, dat3$from_lon, dat3$to_lat, dat3$to_lon)
dev.off()

#######################
## HzMobile
#######################
bsmap <- read.csv('data/hcl_mesos0822_bm', head=F, sep=',')
colnames(bsmap) <- c('bid', 'lacid', 'lon', 'lat')
dat <- read.csv('data/hcl_mesos0822_fm_i24h', head=F, sep=',')
colnames(dat) <- c("interval", "from", "to", "unique", "total")

dat2 <- dat %>% left_join(bsmap, by=c('from' = 'bid')) %>%
  select(-lacid, from_lon=lon, from_lat=lat) %>%
  left_join(bsmap, by=c('to' = 'bid')) %>%
  select(-lacid, to_lon=lon, to_lat=lat)

dat3 <- dat2 %>%
  dplyr::filter(unique>=5)

jpeg('figures/hcl_mesos0822_fm_i24h.jpg', width=6400, height=4800)
draw_flowmap(dat3$from_lat, dat3$from_lon, dat3$to_lat, dat3$to_lon)
dev.off()
