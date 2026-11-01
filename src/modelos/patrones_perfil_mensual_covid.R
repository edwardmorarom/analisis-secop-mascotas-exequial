# D99: perfil mensual (efectos de mes del modelo 2e) con la serie filtrada y sin filtrar; contratos por mes calendario.
suppressMessages(library(MASS))
d0 <- "data/processed/resultados_secop"
b <- read.csv(file.path(d0,"patrones_base.csv"))
res <- list()
for (suf in c("","_sin_filtrar")) {
  cv <- read.csv(file.path(d0,"patrones",paste0("covid_muertes_mensual",suf,".csv")))
  d <- data.frame(mes_txt=cv$mes_txt, y=as.integer(table(factor(b$mes,levels=cv$mes_txt))), lc=cv$log1p_fallecidos)
  d$anio <- factor(substr(d$mes_txt,1,4), levels=c("2025","2020","2021","2022","2023","2024")); d$mes <- factor(substr(d$mes_txt,6,7))
  d <- d[!is.na(d$lc),]
  m <- glm.nb(y ~ mes + anio + lc, data=d, control=glm.control(maxit=200))
  cf <- c(0, coef(m)[grep("^mes",names(coef(m)))]); names(cf) <- levels(d$mes)
  res[[suf]] <- cf
  write.csv(data.frame(mes = names(cf), efecto = as.numeric(cf)), file.path(d0, "patrones", paste0("perfil_mensual_2e", suf, ".csv")), row.names = FALSE)
  cat("serie", suf, "\n"); print(round(cf,2)); cat("top 3 meses del año:", names(sort(cf,decreasing=TRUE))[1:3], "\n")
}
cat("correlacion de perfiles mensuales:", cor(res[[1]],res[[2]]), "\n")
tot <- tapply(b$mes[!is.na(b$mes)], substr(b$mes[!is.na(b$mes)],6,7), length); print(tot)
x <- sort(table(b$mes), decreasing=TRUE)[1:6]; print(x)
