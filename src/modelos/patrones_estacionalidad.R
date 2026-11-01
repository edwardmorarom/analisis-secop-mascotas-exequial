# Estacionalidad de la firma de contratos (D97): Poisson, binomial negativa con mes y año, binomial negativa con armónicos y tendencia.
suppressMessages(library(MASS))
set.seed(2033)
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
dir_fig <- file.path(raiz, "docs", "resultados", "graficos", "patrones")
dir.create(dir_fig, showWarnings = FALSE, recursive = TRUE)
dir.create(dir_out, showWarnings = FALSE, recursive = TRUE)

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE)
conteo <- table(factor(b$mes, levels = format(seq(as.Date("2020-01-01"), as.Date("2025-12-01"), by = "month"), "%Y-%m")))
d <- data.frame(mes_txt = names(conteo), y = as.integer(conteo))
d$anio <- factor(substr(d$mes_txt, 1, 4), levels = c("2025", "2020", "2021", "2022", "2023", "2024"))
d$mes <- factor(substr(d$mes_txt, 6, 7))
d$t <- seq_len(nrow(d))
d$s12 <- sin(2 * pi * d$t / 12); d$c12 <- cos(2 * pi * d$t / 12)
d$s6 <- sin(2 * pi * d$t / 6); d$c6 <- cos(2 * pi * d$t / 6)
d$d2020 <- as.integer(d$anio == "2020")
n <- nrow(d)
cat("meses:", n, "| contratos:", sum(d$y), "| meses con 0:", sum(d$y == 0), "\n")

m1 <- glm(y ~ mes + anio, family = poisson, data = d)
m2 <- glm.nb(y ~ mes + anio, data = d, control = glm.control(maxit = 200))
m3 <- glm.nb(y ~ s12 + c12 + s6 + c6 + t, data = d, control = glm.control(maxit = 200))

mods <- list("1 Poisson (mes y año)" = m1, "2 binomial negativa (mes y año)" = m2, "3 binomial negativa (armónicos y tendencia)" = m3)
comp <- do.call(rbind, lapply(names(mods), function(nm) {
  m <- mods[[nm]]; ll <- logLik(m); k <- attr(ll, "df")
  data.frame(modelo = nm, parametros = k, logLik = as.numeric(ll), BIC = -2 * as.numeric(ll) + k * log(n), AIC = -2 * as.numeric(ll) + 2 * k)
}))
comp$dBIC <- comp$BIC - min(comp$BIC)

asim <- function(x) {m <- mean(x); mean((x - m)^3) / mean((x - m)^2)^1.5}
curt <- function(x) {m <- mean(x); mean((x - m)^4) / mean((x - m)^2)^2 - 3}

# Cameron y Trivedi (1990): ((y - mu)^2 - y) / mu sobre mu, sin intercepto
mu1 <- fitted(m1)
aux <- lm(((d$y - mu1)^2 - d$y) / mu1 ~ 0 + mu1)
ct <- summary(aux)$coefficients
ct_res <- data.frame(alfa = ct[1, 1], error_estandar = ct[1, 2], t = ct[1, 3], p_valor = ct[1, 4])

rq_aleat <- function(m, y) {
  if (inherits(m, "negbin")) {mu <- fitted(m); th <- m$theta; Fy <- pnbinom(y, mu = mu, size = th); Fy1 <- ifelse(y > 0, pnbinom(y - 1, mu = mu, size = th), 0)}
  else {mu <- fitted(m); Fy <- ppois(y, mu); Fy1 <- ifelse(y > 0, ppois(y - 1, mu), 0)}
  qnorm(runif(length(y), Fy1, Fy))
}
diag <- do.call(rbind, lapply(names(mods), function(nm) {
  m <- mods[[nm]]; pr <- residuals(m, type = "pearson"); rq <- rq_aleat(m, d$y)
  data.frame(modelo = nm,
             ljung_box_6_p = Box.test(pr, lag = 6, type = "Ljung-Box")$p.value,
             ljung_box_12_p = Box.test(pr, lag = 12, type = "Ljung-Box")$p.value,
             asimetria_rq = asim(rq), exceso_curtosis_rq = curt(rq), media_rq = mean(rq), sd_rq = sd(rq),
             pearson_chi2_sobre_gl = sum(pr^2) / df.residual(m))
}))
diag$falla_autocorrelacion <- diag$ljung_box_12_p < 0.05
diag$falla_normalidad_rq <- abs(diag$asimetria_rq) > 1 | diag$exceso_curtosis_rq > 3
diag$falla_sobredispersion <- c(ct_res$p_valor < 0.05, FALSE, FALSE)
diag$falla_alguna <- diag$falla_autocorrelacion | diag$falla_normalidad_rq | diag$falla_sobredispersion

# Efecto de 2020 (referencia 2025) en los modelos con año, y sensibilidad del modelo 3
coef_anio <- function(m, nm) {s <- summary(m)$coefficients; f <- s[grepl("^anio", rownames(s)), , drop = FALSE]
  data.frame(modelo = nm, anio = sub("anio", "", rownames(f)), razon_de_tasas_vs_2025 = exp(f[, 1]), estimador = f[, 1], error_estandar = f[, 2], p_valor = f[, 4])}
anios <- rbind(coef_anio(m1, "1 Poisson"), coef_anio(m2, "2 binomial negativa"))
m3_sin2020 <- glm.nb(y ~ s12 + c12 + s6 + c6 + t, data = d[d$anio != "2020", ], control = glm.control(maxit = 200))
m3_ind <- glm.nb(y ~ s12 + c12 + s6 + c6 + t + d2020, data = d, control = glm.control(maxit = 200))
amp <- function(m) {b <- coef(m); c(amplitud_12 = sqrt(b["s12"]^2 + b["c12"]^2), amplitud_6 = sqrt(b["s6"]^2 + b["c6"]^2))}
sens <- do.call(rbind, lapply(list("3 con 2020 (72 meses)" = m3, "3 sin 2020 (60 meses)" = m3_sin2020, "3 con indicadora de 2020 (72 meses)" = m3_ind), function(m) {
  a <- amp(m); s <- summary(m)$coefficients
  data.frame(n = nobs(m), tendencia_por_mes = coef(m)["t"], p_tendencia = s["t", 4], amplitud_12 = a[1], amplitud_6 = a[2],
             razon_2020 = if ("d2020" %in% rownames(s)) exp(coef(m)["d2020"]) else NA, p_2020 = if ("d2020" %in% rownames(s)) s["d2020", 4] else NA,
             BIC = BIC(m), parametros = attr(logLik(m), "df"))
}))
sens$modelo <- rownames(sens); rownames(sens) <- NULL

# Perfil mensual del modelo 2 (razón de tasas de cada mes frente a enero, año de referencia 2025) y del modelo 3 (valor ajustado)
s2 <- summary(m2)$coefficients; mes_efecto <- s2[grepl("^mes", rownames(s2)), , drop = FALSE]
perfil2 <- data.frame(mes = sub("mes", "", rownames(mes_efecto)), razon_vs_enero = exp(mes_efecto[, 1]), p_valor = mes_efecto[, 4])
promedio_mes <- aggregate(y ~ mes, d, mean); names(promedio_mes)[2] <- "promedio_contratos"
d$ajustado_m3 <- fitted(m3); d$ajustado_m2 <- fitted(m2)

png(file.path(dir_fig, "estacionalidad_serie_y_diagnosticos.png"), width = 1500, height = 1000, res = 130)
par(mfrow = c(2, 2), mar = c(4, 4, 3, 1))
plot(d$t, d$y, type = "o", pch = 20, xlab = "mes (1 = enero de 2020)", ylab = "contratos", main = "Conteo mensual y ajustes")
lines(d$t, d$ajustado_m2, col = 2, lwd = 2); lines(d$t, d$ajustado_m3, col = 4, lwd = 2)
legend("topright", c("observado", "modelo 2", "modelo 3"), col = c(1, 2, 4), lty = 1, bty = "n", cex = 0.8)
acf(residuals(m2, type = "pearson"), main = "ACF residuos: modelo 2", lag.max = 24)
acf(residuals(m3, type = "pearson"), main = "ACF residuos: modelo 3", lag.max = 24)
qqnorm(rq_aleat(m3, d$y), main = "Q-Q cuantílicos aleatorizados: modelo 3"); abline(0, 1)
dev.off()

write.csv(d[, c("mes_txt", "y", "ajustado_m2", "ajustado_m3")], file.path(dir_out, "estacionalidad_serie.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(comp, file.path(dir_out, "estacionalidad_bic.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(diag, file.path(dir_out, "estacionalidad_diagnosticos.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(ct_res, file.path(dir_out, "estacionalidad_cameron_trivedi.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(anios, file.path(dir_out, "estacionalidad_efecto_anio.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(sens, file.path(dir_out, "estacionalidad_sensibilidad_2020.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(merge(perfil2, promedio_mes, by = "mes", all = TRUE), file.path(dir_out, "estacionalidad_perfil_mensual.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(data.frame(parametro = c("theta_m2", "theta_m3"), valor = c(m2$theta, m3$theta)), file.path(dir_out, "estacionalidad_theta.csv"), row.names = FALSE, fileEncoding = "UTF-8")
print(comp); print(ct_res); print(diag); print(anios); print(sens); print(merge(perfil2, promedio_mes, by = "mes", all = TRUE))
