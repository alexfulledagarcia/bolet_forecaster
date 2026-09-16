# 🍄 Bolet Forecaster Catalunya

> **Aplicació local de previsió i mapa de probabilitat de bolets comestibles a Catalunya basat en dades meteorològiques obertes (Open-Meteo) i variables ecològiques del territori.**

![Bolet Forecaster Preview](https://img.shields.io/badge/Status-Active-emerald?style=flat-square)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=flat-square)

---

## 📋 Resum del Projecte

**Bolet Forecaster Catalunya** és una aplicació web local interactiva dissenyada per ajudar els boletaires a predir amb rigor científic la florada i probabilitat de trobada dels principals bolets comestibles de Catalunya (*Boletus edulis*, *Lactarius deliciosus/sanguifluus*, *Craterellus lutescens*, *Amanita caesarea*, etc.).

El model combina dades meteorològiques en temps real dels darrers 14-21 dies d'**Open-Meteo** amb les tres dimensions clau de l'ecologia micològica catalana:
1. **Precipitació acumulada i humitat del sòl**: La pluja necessària (*la saó* o *recaldada*, generalment 40-90 mm entre 10 i 20 dies abans) per induir la formació de primordis al miceli subterrani, combinada amb la humitat superficial dels darrers 7 dies.
2. **Topoclimatologia d'Ombra i Orientació (*Obagues vs Solanes*)**: 
   - **Obagues (vessants nord / ombrívols)**: Retenen la humitat de les pluges, tenen menys evaporació solar i són el refugi ideal a finals d'estiu i inici de tardor per a ceps, camagrocs i trompetes de la mort.
   - **Solanes (vessants sud / assolellats)**: Reben màxima insolació. Clau per a espècies termòfiles com l'ou de reig (*Amanita caesarea*) o a finals de novembre/desembre quan les obagues es glaçen.
   - **Fons de vall humits**: Concentració d'humitat i drenatge orgànic.
3. **Massa forestal i simbiosi micorrízica**: Associació directa amb les comunitats d'arbres de Catalunya (pi negre, pi roig, pi blanc, fagedes, rouredes, alzinars, suredes, castanyedes i prats alpins).
4. **Gradient altitudinal**: Pisos de vegetació des del litoral (100 m) fins a l'estatge subalpí pirinenc (2.000 m).

---

## 🍄 Espècies de Bolets Disponibles

L'aplicació permet filtrar i consultar la probabilitat en temps real per a:

| Espècie | Nom Científic | Hàbitat Principal | Pis Altitudinal |
| :--- | :--- | :--- | :--- |
| **Cep (Bolet de bou)** | *Boletus edulis / B. pinophilus / B. aereus* | Pi negre, pi roig, fageda, roureda | 700 m – 2.100 m |
| **Rovelló / Pinetell** | *Lactarius deliciosus / L. sanguifluus* | Pinedes (pi roig, pi blanc, pi negre) | 150 m – 1.850 m |
| **Camagroc** | *Craterellus lutescens* | Pinedes humides amb catifa de molsa (*obagues*) | 300 m – 1.700 m |
| **Trompeta de la mort** | *Craterellus cornucopioides* | Fagedes, rouredes i castanyedes ombrívoles | 350 m – 1.600 m |
| **Rossinyol** | *Cantharellus cibarius* | Boscos caducifolis i mixtos humits | 400 m – 1.750 m |
| **Ou de reig** | *Amanita caesarea* | Alzinars, suredes i castanyedes càlides | 100 m – 950 m |
| **Llenega negra** | *Hygrophorus latitabundus* | Pinedes calcàries de tardor avançada | 350 m – 1.400 m |
| **Cama-sec (Carrereta)**| *Marasmius oreades* | Prats alpins, pastures i clarianes | 500 m – 2.200 m |
| **Fredolic (Negret)** | *Tricholoma terreum* | Pinedes després de les primeres glaçades | 200 m – 1.900 m |

---

## 🚀 Instal·lació i Llançament Local

### 1. Requisits previs
- Python 3.10 o superior instal·lat.

### 2. Creació i activació de l'entorn virtual
```bash
# Navega al directori del projecte
cd /home/fulledaa/Documents/7_Other/bolet_forecaster

# Crea l'entorn virtual (si no està creat)
python3 -m venv .venv

# Activa l'entorn virtual
source .venv/bin/activate

# Instal·la les dependències
pip install -r requirements.txt
```

### 3. Iniciar l'aplicació
Executa el llançador automàtic:
```bash
python3 run.py
```
O amb arguments personalitzats:
```bash
python3 run.py --port 8000 --reload
```

Obre el teu navegador a:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🗺️ Funcionalitats de la Interfície

1. **Mapa Interactiu de Catalunya**:
   - Selector de capes cartogràfiques: *Fosc (CartoDB Dark)*, *Topogràfic (OpenStreetMap)* i *Satèl·lit (Esri)*.
   - **Capa de calor dinàmica (Heatmap)**: Mostra visualment les concentracions de florada de l'espècie triada arreu de Catalunya.
   - Marcadors interactius que polsen a les zones amb probabilitat alta/òptima.
2. **Selector d'Espècies**:
   - Canvia instantàniament de bolet amb un sol clic. El mapa i els rànquings s'actualitzen al moment.
3. **Inspector Explicatiu de Zona (*Explainability Panel*)**:
   - Fes clic a qualsevol punt del territori català o sobre un massís conegut (Cadí, Rasos de Peguera, Pedraforca, Camprodon, Montseny, Guilleries, Prades, Els Ports, etc.).
   - Es desplega un calaix d'anàlisi amb:
     - **Índex de Probabilitat**: 0-100% amb qualificació (*Excel·lent*, *Favorable*, *Moderada*, *Baixa*).
     - **Raonament en Llenguatge Natural**: Explicació precisa de per què s'ha produït o no la florada.
     - **Desglossament de 6 factors**: Precipitació 14d/7d, humitat de sòl, règim tèrmic, hàbitat vegetal, altitud i efecte d'ombra/obaga.
     - **Gràfic d'evolució meteorològica (14 dies)**: Barres de pluja diària acumulada i corbes de temperatura màxima i mínima.
     - **Consells per al boletaire**: Estratègia de cerca al terreny.
     - **Alerta de toxicitat**: Precaucions de confusions perilloses (ex: *Amanita phalloides*, *Tylopilus felleus*, *Omphalotus olearius*).
4. **Cerca i Filtre per Comarca**:
   - Filtra fàcilment per comarques com Berguedà, Ripollès, Osona, Cerdanya, etc.
5. **Actualització en temps real**:
   - El botó **"Actualitza Dades (Open-Meteo)"** connecta amb l'API oberta per refrescar les pluges i temperatures més recents del territori.

---

## 📡 Endpoints de l'API REST

- `GET /api/species` — Retorna el catàleg complet d'espècies amb paràmetres ecològics.
- `GET /api/comarques` — Llistat de comarques cobertes pel model.
- `GET /api/forecast?species_id=cep&comarca=...` — Predicció territorial completa, punts del mapa i dades per al heatmap.
- `GET /api/zone/{zone_id}?species_id=cep` — Detall profund d'una zona concreta amb explicació i sèrie temporal de 17 dies.
- `GET /api/nearest-zone?lat=42.14&lon=1.76&species_id=cep` — Cerca per coordenades geogràfiques quan l'usuari clica al mapa.
- `POST /api/weather/refresh` — Força la descàrrega i actualització de dades des d'Open-Meteo.

---

## 🧪 Execució de Tests

L'aplicació compta amb una suite de proves unitàries i d'integració:
```bash
.venv/bin/python3 -m unittest discover tests
```
Totes les proves verifiquen el càlcul matemàtic de la probabilitat, els llindars ecològics, la gestió de la memòria cau i el funcionament de l'API HTTP.

