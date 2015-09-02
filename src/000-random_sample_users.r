library(dplyr)
library(omniR)

users.all <- readRDS("rdata/hz_sample_users.rds")
bs.all <- readRDS("rdata/hz_bsmap.rds")

sample.id <- sample(unique(users.all$uid), 100)
users.sample <- subset(users.all, uid %in% sample.id)
users.sample$uid <- seq_unique(users.sample$uid)

users <- users.sample %>%
  left_join(bs.all, by=c("bid")) %>%
  select(uid, time, bid, lon, lat)

users$bid <- seq_unique(users$bid)
users <- users[order(users$uid, users$time),]
colnames(users) <- c("id", "time", "loc", "lon", "lat")

save(users, file="rdata/movement.rda")