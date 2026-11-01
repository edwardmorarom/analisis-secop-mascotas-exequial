# Valor del contrato (D97): lineal, mixto lineal y gamma log mixto; BIC en escala del valor, diagnósticos y validación cruzada por entidad.
suppressMessages({library(lme4); library(car)})
set.seed(2033)
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
dir_fig <- file.path(raiz, "docs", "resultados", "graficos", "patrones")
dir.create(dir_fig, showWarnings = FALSE, recursive = TRUE)
dir.create(dir_out, showWarnings = FALSE, recursive = TRUE)

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
n_total <- nrow(b)
b <- b[!is.na(b$valor_constante_2025) & b$valor_constante_2025 > 0, ]
cat("contratos con valor <= 0 o nulo, excluidos:", n_total - nrow(b), "\n")
b$ly <- log(b$valor_constante_2025)
b$y <- b$valor_constante_2025
for (v in c("tipo_entidad", "modalidad_grupo", "fuente")) b[[v]] <- relevel(factor(b[[v]]), ref = names(sort(table(b[[v]]), decreasing = TRUE))[1])
b$anio <- factor(b$anio)
b$entidad_id <- factor(b$entidad_id)
comp <- c("inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
efectos <- paste(c("tipo_entidad", "modalidad_grupo", comp, "anio", "fuente"), collapse = " + ")
f_fijo <- as.formula(paste("ly ~", efectos))
f_mixto <- as.formula(paste("ly ~", efectos, "+ (1 | entidad_id)"))
f_gamma <- as.formula(paste("y ~", efectos, "+ (1 | entidad_id)"))
n <- nrow(b)
sum_ly <- sum(b$ly)

m1 <- lm(f_fijo, b)
m2 <- lmer(f_mixto, b, REML = FALSE, control = lmerControl(optimizer = "bobyqa"))
m3 <- tryCatch(glmer(f_gamma, b, family = Gamma(link = "log"), control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))),
               error = function(e) {cat("glmer falló:", conditionMessage(e), "\n"); NULL})

p_fijos <- length(coef(m1))
ll1_log <- as.numeric(logLik(m1)); ll2_log <- as.numeric(logLik(m2))
k1 <- p_fijos + 1; k2 <- p_fijos + 2
filas <- list(
  data.frame(modelo = "1 lineal", escala_original = "log", logLik_log = ll1_log, logLik_valor = ll1_log - sum_ly, parametros = k1),
  data.frame(modelo = "2 lineal mixto (entidad)", escala_original = "log", logLik_log = ll2_log, logLik_valor = ll2_log - sum_ly, parametros = k2))
if (!is.null(m3)) {
  ll3 <- as.numeric(logLik(m3))
  filas[[3]] <- data.frame(modelo = "3 gamma log mixto (entidad)", escala_original = "valor", logLik_log = ll3 + sum_ly, logLik_valor = ll3, parametros = p_fijos + 2)
}
comp_bic <- do.call(rbind, filas)
comp_bic$BIC <- -2 * comp_bic$logLik_valor + comp_bic$parametros * log(n)
comp_bic$AIC <- -2 * comp_bic$logLik_valor + 2 * comp_bic$parametros
comp_bic$dBIC <- comp_bic$BIC - min(comp_bic$BIC)
comp_bic$n <- n

# Gamma: dispersión (phi) y residuos cuantílicos condicionales
if (!is.null(m3)) {
  mu3 <- fitted(m3)
  phi3 <- sigma(m3)^2
  shape3 <- 1 / phi3
  rq3 <- qnorm(pgamma(b$y, shape = shape3, scale = mu3 * phi3))
  rq3[!is.finite(rq3)] <- NA
}

asim <- function(x) {x <- x[is.finite(x)]; m <- mean(x); mean((x - m)^3) / mean((x - m)^2)^1.5}
curt <- function(x) {x <- x[is.finite(x)]; m <- mean(x); mean((x - m)^4) / mean((x - m)^2)^2 - 3}

diag_fila <- function(nombre, res, aj, cook = NA, gvif = NA) {
  data.frame(modelo = nombre, asimetria_residuos = asim(res), exceso_curtosis = curt(res),
             spearman_abs_res_ajustado = suppressWarnings(cor(abs(res), aj, method = "spearman", use = "complete.obs")),
             cook_maximo = cook, gvif_maximo = gvif)
}
v <- vif(m1)
gv1 <- if (is.matrix(v)) max(v[, "GVIF^(1/(2*Df))"]) else max(v)
v2 <- tryCatch(vif(m2), error = function(e) NULL)
gv2 <- if (is.null(v2)) NA else if (is.matrix(v2)) max(v2[, "GVIF^(1/(2*Df))"]) else max(v2)
cook1 <- max(cooks.distance(m1))
r1 <- rstandard(m1)
r2 <- resid(m2, type = "pearson")
dg <- rbind(diag_fila("1 lineal", r1, fitted(m1), cook1, gv1),
            diag_fila("2 lineal mixto (entidad)", r2, fitted(m2), NA, gv2))
if (!is.null(m3)) dg <- rbind(dg, diag_fila("3 gamma log mixto (entidad)", rq3, log(fitted(m3)), NA, gv2))
dg$falla_normalidad <- abs(dg$asimetria_residuos) > 1 | dg$exceso_curtosis > 3
dg$falla_varianza <- abs(dg$spearman_abs_res_ajustado) > 0.30
dg$falla_cook <- !is.na(dg$cook_maximo) & dg$cook_maximo > 1
dg$falla_colinealidad <- !is.na(dg$gvif_maximo) & dg$gvif_maximo > sqrt(10)
dg$falla_alguna <- dg$falla_normalidad | dg$falla_varianza | dg$falla_cook | dg$falla_colinealidad
dg$cook_mayor_4_sobre_n_modelo1 <- c(sum(cooks.distance(m1) > 4 / n), NA, NA)[seq_len(nrow(dg))]

# ICC (modelo nulo con la misma estructura) y del modelo con covariables
vc <- as.data.frame(VarCorr(m2))
icc_cond <- vc$vcov[1] / (vc$vcov[1] + vc$vcov[2])
m0 <- lmer(ly ~ 1 + (1 | entidad_id), b, REML = FALSE)
vc0 <- as.data.frame(VarCorr(m0))
icc_nulo <- vc0$vcov[1] / (vc0$vcov[1] + vc0$vcov[2])
icc <- data.frame(icc_nulo = icc_nulo, icc_con_covariables = icc_cond, entidades = nlevels(b$entidad_id),
                  var_entidad = vc$vcov[1], var_residual = vc$vcov[2])
if (!is.null(m3)) {
  re3 <- as.data.frame(VarCorr(m3)); icc$icc_gamma_escala_latente <- re3$vcov[1] / (re3$vcov[1] + log(1 + phi3))
  icc$dispersion_gamma <- phi3
}

# Figuras
png(file.path(dir_fig, "valor_qq_y_residuos.png"), width = 1500, height = 1000, res = 130)
par(mfrow = c(2, 3), mar = c(4, 4, 3, 1))
qqnorm(r1, main = "Q-Q: lineal"); qqline(r1)
qqnorm(r2, main = "Q-Q: lineal mixto"); qqline(r2)
if (!is.null(m3)) {qqnorm(rq3, main = "Q-Q: gamma (cuantílicos)"); qqline(rq3)} else plot.new()
plot(fitted(m1), r1, pch = 20, cex = 0.4, main = "Residuos vs ajustados: lineal", xlab = "ajustado", ylab = "residuo"); abline(h = 0, col = 2)
plot(fitted(m2), r2, pch = 20, cex = 0.4, main = "Residuos vs ajustados: mixto", xlab = "ajustado", ylab = "residuo"); abline(h = 0, col = 2)
if (!is.null(m3)) {plot(log(fitted(m3)), rq3, pch = 20, cex = 0.4, main = "Residuos vs ajustados: gamma", xlab = "log ajustado", ylab = "residuo cuantílico"); abline(h = 0, col = 2)} else plot.new()
dev.off()
png(file.path(dir_fig, "valor_cook_y_efectos_aleatorios.png"), width = 1200, height = 500, res = 130)
par(mfrow = c(1, 2), mar = c(4, 4, 3, 1))
plot(cooks.distance(m1), type = "h", main = "Distancia de Cook: lineal", ylab = "Cook", xlab = "contrato")
re <- ranef(m2)$entidad_id[, 1]
qqnorm(re, main = "Q-Q: efectos aleatorios (mixto)"); qqline(re)
dev.off()

# Validación cruzada de 5 pliegues agrupada por entidad
ent <- levels(b$entidad_id)
pliegue_ent <- setNames(sample(rep(1:5, length.out = length(ent))), ent)
b$pliegue <- pliegue_ent[as.character(b$entidad_id)]
cv <- data.frame()
for (p in 1:5) {
  tr <- b[b$pliegue != p, ]; te <- b[b$pliegue == p, ]
  for (v in c("tipo_entidad", "modalidad_grupo")) {
    ok <- te[[v]] %in% unique(tr[[v]]); te <- te[ok, ]
  }
  a1 <- lm(f_fijo, tr)
  a2 <- lmer(f_mixto, tr, REML = FALSE, control = lmerControl(optimizer = "bobyqa"))
  pr <- list("1 lineal" = predict(a1, te), "2 lineal mixto (entidad)" = predict(a2, te, re.form = NA, allow.new.levels = TRUE))
  if (!is.null(m3)) {
    a3 <- tryCatch(glmer(f_gamma, tr, family = Gamma(link = "log"), control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))), error = function(e) NULL)
    if (!is.null(a3)) {
      k <- 1 / sigma(a3)^2
      pr[["3 gamma log mixto (entidad)"]] <- predict(a3, te, re.form = NA, allow.new.levels = TRUE, type = "link") + digamma(k) - log(k)
    }
  }
  for (nm in names(pr)) cv <- rbind(cv, data.frame(modelo = nm, pliegue = p, n_prueba = nrow(te), sse = sum((te$ly - pr[[nm]])^2), sae = sum(abs(te$ly - pr[[nm]]))))
}
cv_res <- aggregate(cbind(sse, sae, n_prueba) ~ modelo, cv, sum)
cv_res$rmse_log <- sqrt(cv_res$sse / cv_res$n_prueba)
cv_res$mae_log <- cv_res$sae / cv_res$n_prueba
cv_res <- cv_res[, c("modelo", "n_prueba", "rmse_log", "mae_log")]

# Coeficientes del modelo mixto (descriptivo)
co <- as.data.frame(summary(m2)$coefficients)
co$termino <- rownames(co)
rownames(co) <- NULL
conv3 <- if (is.null(m3)) "no ajustó" else paste(unlist(m3@optinfo$conv$lme4$messages), collapse = "; ")

write.csv(comp_bic, file.path(dir_out, "valor_bic.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(dg, file.path(dir_out, "valor_diagnosticos.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(icc, file.path(dir_out, "valor_icc.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(cv_res, file.path(dir_out, "valor_validacion_cruzada.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(co, file.path(dir_out, "valor_coeficientes_mixto.csv"), row.names = FALSE, fileEncoding = "UTF-8")
writeLines(c(paste("excluidos_valor_no_positivo:", n_total - nrow(b)), paste("n:", n), paste("convergencia_gamma:", conv3)), file.path(dir_out, "valor_notas.txt"))
print(comp_bic); print(dg); print(icc); print(cv_res); cat("convergencia gamma:", conv3, "\n")
