# D98: estacionalidad con término autorregresivo e indicadora de julio a septiembre de 2020; mismos 71 meses para todos los modelos.
suppressMessages(library(MASS))
set.seed(2034)
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
dir_fig <- file.path(raiz, "docs", "resultados", "graficos", "patrones")

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE)
meses <- format(seq(as.Date("2020-01-01"), as.Date("2025-12-01"), by = "month"), "%Y-%m")
d <- data.frame(mes_txt = meses, y = as.integer(table(factor(b$mes, levels = meses))))
d$anio <- factor(substr(d$mes_txt, 1, 4), levels = c("2025", "2020", "2021", "2022", "2023", "2024"))
d$mes <- factor(substr(d$mes_txt, 6, 7))
d$t <- seq_len(nrow(d))
d$s12 <- sin(2 * pi * d$t / 12); d$c12 <- cos(2 * pi * d$t / 12); d$s6 <- sin(2 * pi * d$t / 6); d$c6 <- cos(2 * pi * d$t / 6)
d$lagy <- c(NA, log(head(d$y, -1) + 1))
d$covid <- as.integer(d$mes_txt %in% c("2020-07", "2020-08", "2020-09"))
d <- d[-1, ]
n <- nrow(d)
cat("meses:", n, "| indicadora covid:", sum(d$covid), "meses\n")

ctrl <- glm.control(maxit = 200)
mods <- list(
  "1 Poisson (mes y año)" = glm(y ~ mes + anio, family = poisson, data = d),
  "2 binomial negativa (mes y año)" = glm.nb(y ~ mes + anio, data = d, control = ctrl),
  "3 binomial negativa (armónicos y tendencia)" = glm.nb(y ~ s12 + c12 + s6 + c6 + t, data = d, control = ctrl),
  "2b binomial negativa (mes, año, autorregresivo y COVID)" = glm.nb(y ~ mes + anio + lagy + covid, data = d, control = ctrl),
  "3b binomial negativa (armónicos, tendencia, autorregresivo y COVID)" = glm.nb(y ~ s12 + c12 + s6 + c6 + t + lagy + covid, data = d, control = ctrl))

asim <- function(x) {m <- mean(x); mean((x - m)^3) / mean((x - m)^2)^1.5}
curt <- function(x) {m <- mean(x); mean((x - m)^4) / mean((x - m)^2)^2 - 3}
rq_aleat <- function(m, y) {
  mu <- fitted(m)
  if (inherits(m, "negbin")) {th <- m$theta; Fy <- pnbinom(y, mu = mu, size = th); Fy1 <- ifelse(y > 0, pnbinom(y - 1, mu = mu, size = th), 0)}
  else {Fy <- ppois(y, mu); Fy1 <- ifelse(y > 0, ppois(y - 1, mu), 0)}
  qnorm(runif(length(y), Fy1, Fy))
}
comp <- do.call(rbind, lapply(names(mods), function(nm) {ll <- logLik(mods[[nm]]); k <- attr(ll, "df")
  data.frame(modelo = nm, parametros = k, logLik = as.numeric(ll), BIC = -2 * as.numeric(ll) + k * log(n), AIC = -2 * as.numeric(ll) + 2 * k)}))
comp$dBIC <- comp$BIC - min(comp$BIC)

mu1 <- fitted(mods[[1]])
ct <- summary(lm(((d$y - mu1)^2 - d$y) / mu1 ~ 0 + mu1))$coefficients
ct_res <- data.frame(alfa = ct[1, 1], error_estandar = ct[1, 2], t = ct[1, 3], p_valor = ct[1, 4])
diag <- do.call(rbind, lapply(seq_along(mods), function(i) {
  m <- mods[[i]]; pr <- residuals(m, type = "pearson"); rq <- rq_aleat(m, d$y)
  data.frame(modelo = names(mods)[i], ljung_box_6_p = Box.test(pr, lag = 6, type = "Ljung-Box")$p.value, ljung_box_12_p = Box.test(pr, lag = 12, type = "Ljung-Box")$p.value,
             asimetria_rq = asim(rq), exceso_curtosis_rq = curt(rq), sd_rq = sd(rq), pearson_chi2_sobre_gl = sum(pr^2) / df.residual(m))
}))
diag$falla_autocorrelacion <- diag$ljung_box_12_p < 0.05
diag$falla_normalidad_rq <- abs(diag$asimetria_rq) > 1 | diag$exceso_curtosis_rq > 3
diag$falla_sobredispersion <- c(ct_res$p_valor < 0.05, rep(FALSE, length(mods) - 1))
diag$falla_alguna <- diag$falla_autocorrelacion | diag$falla_normalidad_rq | diag$falla_sobredispersion

# Newey-West (Bartlett, rezago floor(4 (T/100)^(2/9))) para glm.nb
L <- floor(4 * (n / 100)^(2 / 9))
nw <- function(m) {
  X <- model.matrix(m); mu <- fitted(m); th <- m$theta
  s <- X * ((d$y - mu) / (1 + mu / th))
  M <- crossprod(s)
  for (l in 1:L) {G <- crossprod(s[(l + 1):n, , drop = FALSE], s[1:(n - l), , drop = FALSE]); M <- M + (1 - l / (L + 1)) * (G + t(G))}
  V <- vcov(m); Vn <- V %*% M %*% V
  se <- sqrt(diag(Vn)); est <- coef(m)
  data.frame(termino = names(est), estimador = est, se_modelo = sqrt(diag(V)), se_newey_west = se, p_modelo = 2 * pnorm(-abs(est / sqrt(diag(V)))), p_newey_west = 2 * pnorm(-abs(est / se)))
}
coefs <- do.call(rbind, lapply(c(4, 5), function(i) cbind(modelo = names(mods)[i], nw(mods[[i]]))))
write.csv(comp, file.path(dir_out, "estacionalidad_d98_bic.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(diag, file.path(dir_out, "estacionalidad_d98_diagnosticos.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(coefs, file.path(dir_out, "estacionalidad_d98_coeficientes.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(data.frame(rezago_newey_west = L, n = n, ct_alfa = ct_res$alfa, ct_p = ct_res$p_valor), file.path(dir_out, "estacionalidad_d98_notas.csv"), row.names = FALSE)
png(file.path(dir_fig, "estacionalidad_d98_acf.png"), width = 1500, height = 500, res = 130)
par(mfrow = c(1, 3), mar = c(4, 4, 3, 1))
for (i in c(2, 4, 5)) acf(residuals(mods[[i]], type = "pearson"), main = paste("ACF residuos:", substr(names(mods)[i], 1, 2)), lag.max = 24)
dev.off()
print(comp); print(diag); print(coefs[coefs$termino %in% c("lagy", "covid", "t", "s12", "c12"), ])
