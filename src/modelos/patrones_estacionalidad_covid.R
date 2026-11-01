# D99 (exploratorio, continúa D98): estacionalidad con muertes COVID mensuales (log + 1) e indicadora sobre el percentil 75, con y sin el primer mes.
suppressMessages(library(MASS))
set.seed(2034)
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
dir_fig <- file.path(raiz, "docs", "resultados", "graficos", "patrones")

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE)
cv <- read.csv(file.path(dir_out, "covid_muertes_mensual.csv"), stringsAsFactors = FALSE)
meses <- cv$mes_txt
d <- data.frame(mes_txt = meses, y = as.integer(table(factor(b$mes, levels = meses))))
d$anio <- factor(substr(d$mes_txt, 1, 4), levels = c("2025", "2020", "2021", "2022", "2023", "2024"))
d$mes <- factor(substr(d$mes_txt, 6, 7))
d$t <- seq_len(nrow(d))
d$s12 <- sin(2 * pi * d$t / 12); d$c12 <- cos(2 * pi * d$t / 12); d$s6 <- sin(2 * pi * d$t / 6); d$c6 <- cos(2 * pi * d$t / 6)
d$lagy <- c(NA, log(head(d$y, -1) + 1))
d$lcovid <- cv$log1p_fallecidos
d$alto <- cv$sobre_p75
d$jas2020 <- as.integer(d$mes_txt %in% c("2020-07", "2020-08", "2020-09"))
ctrl <- glm.control(maxit = 200)

asim <- function(x) {m <- mean(x); mean((x - m)^3) / mean((x - m)^2)^1.5}
curt <- function(x) {m <- mean(x); mean((x - m)^4) / mean((x - m)^2)^2 - 3}
rq_aleat <- function(m, y) {mu <- fitted(m); th <- m$theta; qnorm(runif(length(y), ifelse(y > 0, pnbinom(y - 1, mu = mu, size = th), 0), pnbinom(y, mu = mu, size = th)))}

nw_cov <- function(m, dat) {
  n <- nrow(dat); L <- floor(4 * (n / 100)^(2 / 9))
  X <- model.matrix(m); mu <- fitted(m); th <- m$theta
  s <- X * ((dat$y - mu) / (1 + mu / th))
  M <- crossprod(s)
  for (l in 1:L) {G <- crossprod(s[(l + 1):n, , drop = FALSE], s[1:(n - l), , drop = FALSE]); M <- M + (1 - l / (L + 1)) * (G + t(G))}
  V <- vcov(m); V %*% M %*% V
}
wald_estacional <- function(m, dat) {
  nom <- names(coef(m)); idx <- which(grepl("^mes", nom) | nom %in% c("s12", "c12", "s6", "c6"))
  if (length(idx) == 0) return(c(NA, NA, NA))
  V <- nw_cov(m, dat)[idx, idx, drop = FALSE]; b <- coef(m)[idx]
  W <- as.numeric(t(b) %*% solve(V) %*% b)
  c(estadistico = W, gl = length(idx), p = pchisq(W, length(idx), lower.tail = FALSE))
}
amplitud12 <- function(m) {b <- coef(m); if (all(c("s12", "c12") %in% names(b))) sqrt(b["s12"]^2 + b["c12"]^2) else NA_real_}

formulas <- list(
  "2 mes y año" = y ~ mes + anio,
  "3 armónicos y tendencia" = y ~ s12 + c12 + s6 + c6 + t,
  "2b mes, año, AR y jul–sep 2020 (D98)" = y ~ mes + anio + lagy + jas2020,
  "3b armónicos, tendencia, AR y jul–sep 2020 (D98)" = y ~ s12 + c12 + s6 + c6 + t + lagy + jas2020,
  "2c mes, año y COVID" = y ~ mes + anio + lcovid + alto,
  "3c armónicos, tendencia y COVID" = y ~ s12 + c12 + s6 + c6 + t + lcovid + alto,
  "2d mes, año, AR y COVID" = y ~ mes + anio + lagy + lcovid + alto,
  "3d armónicos, tendencia, AR y COVID" = y ~ s12 + c12 + s6 + c6 + t + lagy + lcovid + alto)
# Muestras: 72 meses (sin término autorregresivo) y 71 meses (sin el primer mes), donde caben todos los modelos
panel <- list("72 meses" = list(datos = d, modelos = c(1, 2, 5, 6)), "71 meses (sin enero de 2020)" = list(datos = d[-1, ], modelos = 1:8))

resultados <- list(); coefs <- list()
for (nm in names(panel)) {
  dat <- panel[[nm]]$datos; n <- nrow(dat)
  for (i in panel[[nm]]$modelos) {
    f <- formulas[[i]]
    m <- glm.nb(f, data = dat, control = ctrl)
    pr <- residuals(m, type = "pearson"); rq <- rq_aleat(m, dat$y)
    w <- wald_estacional(m, dat)
    ll <- logLik(m); k <- attr(ll, "df")
    resultados[[length(resultados) + 1]] <- data.frame(muestra = nm, n = n, modelo = names(formulas)[i], parametros = k, BIC = -2 * as.numeric(ll) + k * log(n),
      ljung_box_6_p = Box.test(pr, lag = 6, type = "Ljung-Box")$p.value, ljung_box_12_p = Box.test(pr, lag = 12, type = "Ljung-Box")$p.value,
      asimetria_rq = asim(rq), exceso_curtosis_rq = curt(rq), wald_estacional = w[1], wald_gl = w[2], wald_p_newey_west = w[3], amplitud_12 = amplitud12(m))
    Vn <- nw_cov(m, dat); se_nw <- sqrt(diag(Vn)); est <- coef(m)
    cc <- data.frame(muestra = nm, modelo = names(formulas)[i], termino = names(est), estimador = est, se_modelo = sqrt(diag(vcov(m))), se_newey_west = se_nw,
                     p_modelo = 2 * pnorm(-abs(est / sqrt(diag(vcov(m))))), p_newey_west = 2 * pnorm(-abs(est / se_nw)))
    coefs[[length(coefs) + 1]] <- cc[!grepl("^(mes|anio|\\(Intercept\\))", cc$termino), ]
  }
}
res <- do.call(rbind, resultados)
res$dBIC <- ave(res$BIC, res$muestra, FUN = function(x) x - min(x))
res$falla_autocorrelacion <- res$ljung_box_12_p < 0.05
res$falla_normalidad_rq <- abs(res$asimetria_rq) > 1 | res$exceso_curtosis_rq > 3
cf <- do.call(rbind, coefs)
# correlación entre los dos términos COVID
cor_cov <- data.frame(correlacion_log_muertes_e_indicadora = cor(d$lcovid, d$alto), correlacion_log_muertes_con_jul_sep_2020 = cor(d$lcovid, d$jas2020))
write.csv(res, file.path(dir_out, "estacionalidad_covid_modelos.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(cf, file.path(dir_out, "estacionalidad_covid_coeficientes.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(cor_cov, file.path(dir_out, "estacionalidad_covid_correlacion.csv"), row.names = FALSE, fileEncoding = "UTF-8")
print(res[, c("muestra", "modelo", "parametros", "BIC", "dBIC", "ljung_box_12_p", "asimetria_rq", "exceso_curtosis_rq", "wald_p_newey_west", "amplitud_12")], digits = 3)
print(cf[cf$termino %in% c("lagy", "lcovid", "alto", "jas2020"), ], digits = 3)
print(cor_cov)
