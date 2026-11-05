import pandas as pd

from src.etl.clasificar_places import plano
from src.etl.comun import RAIZ
from src.etl.places import divipola

CARPETA = RAIZ / "data/raw/trends"
TERMINOS_D08 = {"cremacion": "cremación de mascotas", "funeraria": "funeraria de mascotas"}
ALIAS = {"san andres y providencia": "archipielago de san andres"}


def leer(ruta):
    """Lee un CSV de Trends: devuelve el término que trae el encabezado y los datos (valor vacío = sin interés detectable)."""
    d = pd.read_csv(ruta, skiprows=2)
    termino = d.columns[1].split(":")[0].strip()
    d.columns = [d.columns[0], "valor"]
    return termino, d


def codigos_departamento():
    d = divipola().drop_duplicates("cod_dpto")
    return {plano(r.departamento): r.cod_dpto for r in d.itertuples()}


def cod_dpto(nombre, codigos):
    clave = ALIAS.get(plano(nombre), plano(nombre))
    hallados = [c for n, c in codigos.items() if n.startswith(clave)]
    return hallados[0] if len(hallados) == 1 else None


def tabla_departamentos(carpeta=CARPETA):
    """Interés detectable (sí/no) por departamento y término. `termino_valido` es falso si el encabezado del archivo
    no es el término de D08 que indica su nombre (p. ej. cementerio de mascotas, excluido)."""
    codigos = codigos_departamento()
    filas = []
    for clave, esperado in TERMINOS_D08.items():
        for ruta in sorted(carpeta.glob(f"trends_{clave}_mascotas_subregion_*.csv")):
            termino, d = leer(ruta)
            valido = plano(termino) == plano(esperado)
            for r in d.itertuples():
                filas.append({"termino": esperado, "termino_encabezado": termino, "termino_valido": valido,
                              "departamento": r.Región, "cod_dpto": cod_dpto(r.Región, codigos),
                              "indice": r.valor, "interes_detectable": bool(pd.notna(r.valor)), "archivo": ruta.name})
    return pd.DataFrame(filas)


def serie_nacional(carpeta=CARPETA):
    series = []
    for clave, esperado in TERMINOS_D08.items():
        for ruta in sorted(carpeta.glob(f"trends_{clave}_mascotas_tiempo_*.csv")):
            termino, d = leer(ruta)
            d = d.rename(columns={"Semana": "semana"}).assign(
                termino=esperado, termino_encabezado=termino, termino_valido=plano(termino) == plano(esperado),
                interes_detectable=lambda x: x["valor"].fillna(0) > 0, archivo=ruta.name)
            series.append(d)
    return pd.concat(series, ignore_index=True)


def main():
    destino = RAIZ / "data/processed"
    dep, serie = tabla_departamentos(), serie_nacional()
    dep.to_csv(destino / "trends_departamentos.csv", index=False, encoding="utf-8-sig")
    serie.to_csv(destino / "trends_serie_nacional.csv", index=False, encoding="utf-8-sig")
    print(dep.groupby(["termino", "termino_valido"]).agg(departamentos=("departamento", "size"), detectables=("interes_detectable", "sum"),
                                                          sin_codigo=("cod_dpto", lambda c: int(c.isna().sum()))))
    print(serie.groupby(["termino", "termino_valido"]).agg(semanas=("semana", "size"), con_interes=("interes_detectable", "sum")))


if __name__ == "__main__":
    main()
