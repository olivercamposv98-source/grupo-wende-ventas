# Grupo Wende · Dashboard Ejecutivo de Ventas Diarias

Dashboard en **Streamlit** (fondo oscuro, detalles amarillos) para presentar a los dueños las ventas diarias de las **13 tiendas** del grupo: El Chico Fresa (8 sucursales CF), MrBeast Burger (Equipetrol, Norte y Centro), La Happy Hour y Santo Domingo Urubó.

Los datos se leen **en vivo** desde la hoja de Google Sheets «REPORTE DE VENTAS DIARIAS» (export CSV). Si la hoja no está disponible, la app usa el respaldo local `data/ventas_diarias_raw.csv`.

## Estructura del reporte

1. **Resumen ejecutivo** — Ventas MTD, Run Rate (proyección de cierre), total del mes anterior, crecimiento MoM, venta promedio diaria y barra de avance hacia el objetivo (igualar o superar el mes anterior), con el ritmo diario requerido para lograrlo.
2. **Desglose por tienda y marca** — Tabla matricial (mes anterior, mes actual, variación %, run rate, % proyección vs objetivo), recuadros de Top 3 / Bottom 3 y mix de participación por marca con logos.
3. **Tendencia diaria** — Curva diaria del mes actual vs mes anterior y venta promedio por día de la semana, destacando el mejor y el peor día.
4. **KPIs adicionales** — Récord diario, tienda más consistente (menor coeficiente de variación) y mayores subidas/caídas vs el mes anterior.

## Fórmulas exactas

Con `MTD = Σ ventas del mes en curso`, `d = último día con datos`, `D = días calendario del mes`:

| KPI | Fórmula |
|---|---|
| Ventas MTD | `MTD = SUMA(ventas del mes actual)` |
| Run Rate | `Run Rate = (MTD ÷ d) × D` |
| Venta promedio diaria | `MTD ÷ d` |
| Crecimiento MoM proyectado | `(Run Rate ÷ Total mes anterior) − 1` |
| Variación % comparable (por tienda) | `(MTD tienda ÷ ventas de la tienda en los días 1..d del mes anterior) − 1` |
| % Proyección vs objetivo | `Run Rate ÷ Total mes anterior` (objetivo = igualar el mes anterior) |
| Ritmo diario requerido | `(Total mes anterior − MTD) ÷ (D − d)` |
| Mix por marca | `ventas de la marca ÷ ventas totales del mes` |
| Mejor/peor día de la semana | promedio de la venta total diaria agrupada por día de la semana |
| Tienda más consistente | menor `CV = desv. estándar diaria ÷ promedio diario` |

Equivalentes en Google Sheets (rango `A:C` = FECHA, SUCURSAL, VENTA):

```
MTD:        =SUMPRODUCT((MONTH(A2:A)=MES)*(YEAR(A2:A)=AÑO)*C2:C)
Run Rate:   =MTD / DIA_CORTE * DAY(EOMONTH(DATE(AÑO,MES,1),0))
Var % :     =MTD_TIENDA / SUMPRODUCT((B2:B=TIENDA)*(MONTH(A2:A)=MES-1)*(DAY(A2:A)<=DIA_CORTE)*C2:C) - 1
```

## Cómo publicarlo (GitHub → Streamlit Cloud)

1. Crea un repositorio en GitHub y sube todo el contenido de esta carpeta:
   ```bash
   git init
   git add .
   git commit -m "Dashboard ejecutivo Grupo Wende"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/grupo-wende-dashboard.git
   git push -u origin main
   ```
2. Entra a [share.streamlit.io](https://share.streamlit.io), conecta tu cuenta de GitHub y elige el repo, rama `main`, archivo `app.py`.
3. Listo: la app quedará en una URL pública tipo `https://tu-app.streamlit.app`. La hoja debe seguir compartida como «cualquiera con el enlace puede ver» para la lectura en vivo (cache de 10 minutos).

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura de archivos

```
├── app.py                      # Aplicación Streamlit
├── requirements.txt
├── .streamlit/config.toml      # Tema oscuro + amarillo
├── assets/                     # Logos de las marcas y de Grupo Wende
└── data/ventas_diarias_raw.csv # Respaldo local de la hoja
```
