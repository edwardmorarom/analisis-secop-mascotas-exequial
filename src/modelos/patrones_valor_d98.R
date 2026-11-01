# D98: coeficientes del lineal mixto con errores robustos agrupados por entidad (CR1) y del gamma log mixto, para compararlos con la mediana.
suppressMessages(library(lme4))
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
b <- b[!is.na(b$valor_constante_2025) & b$valor_constante_2025 > 0, ]
b$ly <- log(b$valor_constante_2025); b$y <- b$valor_constante_2025
for (v in c("tipo_entidad", "modalidad_grupo", "fuente")) b[[v]] <- relevel(factor(b[[v]]), ref = names(sort(table(b[[v]]), decreasing = TRUE))[1])
b$anio <- factor(b$anio); b$entidad_id <- factor(b$entidad_id)
comp <- c("inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
efectos <- paste(c("tipo_entidad", "modalidad_grupo", comp, "anio", "fuente"), collapse = " + ")
m2 <- lmer(as.formula(paste("ly ~", efectos, "+ (1 | entidad_id)")), b, REML = FALSE, control = lmerControl(optimizer = "bobyqa"))
m3 <- glmer(as.formula(paste("y ~", efectos, "+ (1 | entidad_id)")), b, family = Gamma(link = "log"), control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))

X <- getME(m2, "X"); y <- b$ly; beta <- fixef(m2)
vc <- as.data.frame(VarCorr(m2)); tau2 <- vc$vcov[1]; s2 <- vc$vcov[2]
g <- b$entidad_id; N <- nrow(X); p <- ncol(X); G <- nlevels(g)
A <- matrix(0, p, p); B <- matrix(0, p, p)
vinv_mult <- function(M, ng) (M - tau2 / (s2 + ng * tau2) * matrix(colSums(M), ng, ncol(M), byrow = TRUE)) / s2
partes <- split(seq_len(N), g)
sc <- lapply(partes, function(i) {
  ng <- length(i); Xg <- X[i, , drop = FALSE]; r <- y[i] - Xg %*% beta
  VX <- vinv_mult(Xg, ng); Vr <- vinv_mult(r, ng)
  list(A = crossprod(Xg, VX), s = crossprod(Xg, Vr))
})
for (e in sc) {A <- A + e$A; B <- B + tcrossprod(e$s)}
Ai <- solve(A)
cov_cr1 <- Ai %*% B %*% Ai * (G / (G - 1)) * ((N - 1) / (N - p))
se <- sqrt(diag(cov_cr1)); tval <- beta / se; pval <- 2 * pt(-abs(tval), df = G - 1)
lmm <- data.frame(termino = names(beta), lmm_estimador = unname(beta), lmm_se_robusto = se, lmm_p = pval,
                  lmm_ic_bajo = beta - qt(0.975, G - 1) * se, lmm_ic_alto = beta + qt(0.975, G - 1) * se)
sg <- summary(m3)$coefficients
gam <- data.frame(termino = rownames(sg), gamma_estimador = sg[, 1], gamma_se = sg[, 2], gamma_p = sg[, 4])
gam$gamma_ic_bajo <- gam$gamma_estimador - 1.96 * gam$gamma_se; gam$gamma_ic_alto <- gam$gamma_estimador + 1.96 * gam$gamma_se
write.csv(merge(lmm, gam, by = "termino", sort = FALSE), file.path(dir_out, "valor_d98_lmm_gamma.csv"), row.names = FALSE, fileEncoding = "UTF-8")
cat("entidades:", G, "| n:", N, "\n")
