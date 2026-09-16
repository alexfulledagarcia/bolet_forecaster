import math
from typing import Dict, Any, Tuple
from app.models.species import Species, FactorBreakdown, ZoneExplanation, ZoneForecast, WeatherHistoryPoint


class PredictionModel:
    """
    Scientific ecological forecasting engine for edible mushrooms in Catalonia.
    Integrates meteorological triggers (14d/7d rainfall, soil moisture, temperature regime)
    with environmental covariates (altitude, forest tree symbiosis, and topoclimatic shading: Obaga vs Solana).
    """

    @staticmethod
    def calculate_forecast(zone: Dict[str, Any], weather: Dict[str, Any], species: Species) -> ZoneForecast:
        rain_14d = weather.get("rain_14d_mm", 0.0)
        rain_7d = weather.get("rain_7d_mm", 0.0)
        soil_pct = weather.get("soil_moisture_pct", 25.0)
        temp_mean = weather.get("temp_mean_c", 15.0)
        temp_min = weather.get("temp_min_c", 8.0)
        temp_max = weather.get("temp_max_c", 22.0)
        elev = zone.get("elevation_m", 800)
        aspect = zone.get("aspect", "")
        forest = zone.get("forest_type", "")

        # 1. Rainfall score (0-100)
        rain_score = PredictionModel._calc_rain_score(rain_14d, rain_7d, species)

        # 2. Soil moisture score (0-100)
        soil_score = PredictionModel._calc_soil_score(soil_pct, species)

        # 3. Temperature score (0-100)
        temp_score = PredictionModel._calc_temp_score(temp_mean, temp_min, temp_max, species)

        # 4. Habitat suitability (0-100)
        habitat_score = PredictionModel._calc_habitat_score(forest, species)

        # 5. Elevation suitability (0-100)
        elevation_score = PredictionModel._calc_elevation_score(elev, species)

        # 6. Aspect & Shading score (0-100)
        aspect_score = PredictionModel._calc_aspect_score(aspect, temp_mean, species)

        # Weather composite factor (rain 45%, soil 25%, temp 30%)
        weather_composite = (rain_score * 0.45) + (soil_score * 0.25) + (temp_score * 0.30)

        # Environmental composite (habitat 50%, elevation 30%, aspect 20%)
        env_composite = (habitat_score * 0.50) + (elevation_score * 0.30) + (aspect_score * 0.20)

        # Ecological Limiting Factor (Liebig's Law of the Minimum):
        # A severe deficiency in temperature (frost), rain (drought), or habitat cannot be fully compensated by other variables.
        temp_limit = min(1.0, (temp_score / 50.0) ** 1.25)
        rain_limit = min(1.0, (rain_score / 35.0) ** 1.2)
        env_limit = min(1.0, (habitat_score / 40.0) ** 1.4) * min(1.0, (elevation_score / 35.0) ** 1.3)
        limiting_multiplier = temp_limit * rain_limit * env_limit

        raw_prob = (weather_composite * 0.60 + env_composite * 0.40) * limiting_multiplier
        probability = max(1.0, min(99.0, round(raw_prob, 1)))

        factors = FactorBreakdown(
            rain_score=round(rain_score, 1),
            rain_14d_mm=rain_14d,
            rain_7d_mm=rain_7d,
            soil_score=round(soil_score, 1),
            soil_moisture_pct=soil_pct,
            temp_score=round(temp_score, 1),
            temp_mean_c=temp_mean,
            temp_min_c=temp_min,
            temp_max_c=temp_max,
            habitat_score=round(habitat_score, 1),
            elevation_score=round(elevation_score, 1),
            aspect_score=round(aspect_score, 1)
        )

        rating_ca, rating_en, badge_color = PredictionModel._get_rating_info(probability)

        explanation = PredictionModel._generate_explanation(
            zone, weather, species, factors, probability, rating_ca, rating_en, badge_color
        )

        history_points = [
            WeatherHistoryPoint(**pt) for pt in weather.get("history", [])
        ]

        return ZoneForecast(
            zone_id=zone["id"],
            name=zone["name"],
            comarca=zone["comarca"],
            region=zone["region"],
            lat=zone["lat"],
            lon=zone["lon"],
            elevation_m=elev,
            aspect=aspect,
            forest_type=forest,
            soil_type=zone.get("soil_type", "Neutre"),
            notes=zone.get("notes"),
            probability=probability,
            rating_label=rating_ca,
            factors=factors,
            explanation=explanation,
            history=history_points
        )

    @staticmethod
    def _calc_rain_score(r14: float, r7: float, species: Species) -> float:
        min_14 = species.rain_trigger_14d_min_mm
        opt_low_14, opt_high_14 = species.rain_trigger_14d_optimal_mm
        opt_low_7, opt_high_7 = species.recent_rain_7d_optimal_mm

        # 14d trigger score
        if r14 < min_14:
            s14 = (r14 / max(1.0, min_14)) * 45.0
        elif r14 <= opt_low_14:
            s14 = 45.0 + ((r14 - min_14) / max(1.0, opt_low_14 - min_14)) * 50.0
        elif r14 <= opt_high_14:
            s14 = 95.0 + ((r14 - opt_low_14) / max(1.0, opt_high_14 - opt_low_14)) * 5.0
        else:
            # Saturated / high rain, slight decay but remains favorable
            s14 = max(65.0, 100.0 - (r14 - opt_high_14) * 0.25)

        # 7d recent moisture score
        if r7 < (opt_low_7 * 0.5):
            s7 = (r7 / max(1.0, opt_low_7 * 0.5)) * 40.0
        elif r7 <= opt_low_7:
            s7 = 40.0 + ((r7 - opt_low_7 * 0.5) / max(1.0, opt_low_7 * 0.5)) * 50.0
        elif r7 <= opt_high_7:
            s7 = 90.0 + ((r7 - opt_low_7) / max(1.0, opt_high_7 - opt_low_7)) * 10.0
        else:
            s7 = max(70.0, 100.0 - (r7 - opt_high_7) * 0.3)

        return (s14 * 0.70) + (s7 * 0.30)

    @staticmethod
    def _calc_soil_score(soil_pct: float, species: Species) -> float:
        min_moist = species.min_soil_moisture * 100.0
        opt_low, opt_high = species.optimal_soil_moisture[0] * 100.0, species.optimal_soil_moisture[1] * 100.0

        if soil_pct < min_moist:
            return (soil_pct / max(1.0, min_moist)) * 40.0
        elif soil_pct <= opt_low:
            return 40.0 + ((soil_pct - min_moist) / max(1.0, opt_low - min_moist)) * 50.0
        elif soil_pct <= opt_high:
            return 90.0 + ((soil_pct - opt_low) / max(1.0, opt_high - opt_low)) * 10.0
        else:
            # Super damp/muddy
            return max(75.0, 100.0 - (soil_pct - opt_high) * 0.8)

    @staticmethod
    def _calc_temp_score(t_mean: float, t_min: float, t_max: float, species: Species) -> float:
        opt_l, opt_h = species.optimal_temp_mean_c
        abs_min = species.temp_min_c
        abs_max = species.temp_max_c

        # Mean temp suitability
        if opt_l <= t_mean <= opt_h:
            base_score = 95.0
        elif abs_min <= t_mean < opt_l:
            base_score = 30.0 + ((t_mean - abs_min) / max(0.5, opt_l - abs_min)) * 65.0
        elif opt_h < t_mean <= abs_max:
            base_score = 95.0 - ((t_mean - opt_h) / max(0.5, abs_max - opt_h)) * 65.0
        else:
            base_score = 15.0

        # Frost penalty
        if t_min <= 0.0:
            if species.frost_sensitivity == "extreme":
                base_score *= 0.15
            elif species.frost_sensitivity == "high":
                base_score *= 0.40
            elif species.frost_sensitivity == "medium":
                base_score *= 0.70
            elif species.frost_sensitivity == "low":
                base_score *= 0.90
            elif species.frost_sensitivity == "very_low":
                # Cold is actually a fruit trigger for Fredolic!
                base_score = min(100.0, base_score * 1.1)

        # Extreme heat penalty (>28C)
        if t_max > 28.0 and species.id != "ou_de_reig":
            base_score *= 0.75

        return max(5.0, min(100.0, base_score))

    @staticmethod
    def _calc_habitat_score(forest_type: str, species: Species) -> float:
        # Check direct match
        for hab in species.habitats:
            if hab.lower() in forest_type.lower() or forest_type.lower() in hab.lower():
                return 98.0

        # Partial matches
        is_conifer_species = any("pi" in h.lower() for h in species.habitats)
        is_conifer_forest = "pi" in forest_type.lower()
        is_deciduous_species = any("fageda" in h.lower() or "roure" in h.lower() or "castany" in h.lower() for h in species.habitats)
        is_deciduous_forest = "fageda" in forest_type.lower() or "roure" in forest_type.lower() or "castany" in forest_type.lower()

        if is_conifer_species and is_conifer_forest:
            return 75.0
        if is_deciduous_species and is_deciduous_forest:
            return 75.0

        # Cama-sec in pastures
        if species.id == "camasec" and "prat" in forest_type.lower():
            return 100.0

        return 15.0

    @staticmethod
    def _calc_elevation_score(elev: float, species: Species) -> float:
        opt_l, opt_h = species.optimal_elevation_m
        min_e, max_e = species.elevation_min_m, species.elevation_max_m

        if opt_l <= elev <= opt_h:
            return 98.0
        elif min_e <= elev < opt_l:
            return 40.0 + ((elev - min_e) / max(1.0, opt_l - min_e)) * 55.0
        elif opt_h < elev <= max_e:
            return 95.0 - ((elev - opt_h) / max(1.0, max_e - opt_h)) * 55.0
        else:
            # Beyond limits
            dist = min(abs(elev - min_e), abs(elev - max_e))
            return max(5.0, 30.0 - (dist / 100.0) * 8.0)

    @staticmethod
    def _calc_aspect_score(aspect: str, temp_mean: float, species: Species) -> float:
        """
        Shading / Aspect modifier:
        In Catalan mushroom hunting tradition:
        - Obaga (North / shaded): Retains humidity and stays cool. Highly favored in late summer
          and early autumn (Sep/Oct) for Ceps, Camagrocs, and Trompetes.
        - Solana (South / sunny): Absorbs heat. Highly favored by thermophilic species (Ou de reig)
          and late season (Nov/Dec) when north slopes freeze.
        - Fons de vall: Humid, deep moss layer, sheltered from desiccating winds.
        """
        is_obaga = "obaga" in aspect.lower()
        is_solana = "solana" in aspect.lower()
        is_vall = "vall" in aspect.lower()

        if species.id == "ou_de_reig":
            # Thermophilic loves sun
            if is_solana:
                return 98.0
            elif is_vall:
                return 75.0
            else:
                return 50.0

        if species.id in ["camagroc", "trompeta", "cep"]:
            # Moisture and shade lovers
            if is_obaga:
                return 98.0
            elif is_vall:
                return 92.0
            elif is_solana:
                return 55.0 if temp_mean > 15.0 else 70.0

        # General species
        if temp_mean > 17.0:
            # Warm period: Obaga shields from drying out
            if is_obaga or is_vall:
                return 95.0
            else:
                return 60.0
        elif temp_mean < 8.0:
            # Cold period: Solana gets warm sunshine
            if is_solana:
                return 95.0
            else:
                return 65.0
        else:
            return 85.0

    @staticmethod
    def _get_rating_info(prob: float) -> Tuple[str, str, str]:
        if prob >= 85.0:
            return ("Excel·lent (Molt Alta)", "Excellent (Very High)", "#10B981")  # Vibrant Green
        elif prob >= 70.0:
            return ("Favorable / Bona", "Favorable / Good", "#EAB308")  # Yellow (~75%)
        elif prob >= 55.0:
            return ("Moderada", "Moderate", "#F97316")  # Orange
        else:
            return ("Baixa / Mínima", "Low / Minimum", "#EF4444")  # Red (<=50%)

    @staticmethod
    def _generate_explanation(
        zone: Dict[str, Any],
        weather: Dict[str, Any],
        species: Species,
        factors: FactorBreakdown,
        prob: float,
        rating_ca: str,
        rating_en: str,
        badge_color: str
    ) -> ZoneExplanation:
        z_name = zone["name"]
        aspect = zone["aspect"]
        forest = zone["forest_type"]
        elev = zone["elevation_m"]

        # Rain explanation
        r14 = factors.rain_14d_mm
        r7 = factors.rain_7d_mm
        if factors.rain_score >= 80:
            rain_det = (
                f"Pluges idònies: s'han acumulat {r14} mm en els darrers 14 dies (i {r7} mm els últims 7 dies). "
                f"Això supera amb escreix el llindar mínim de fructificació ({species.rain_trigger_14d_min_mm} mm), "
                f"iniciant el cicle biològic de la florada ('la saó')."
            )
        elif factors.rain_score >= 50:
            rain_det = (
                f"Precipitació moderada: {r14} mm acumulats en 14 dies ({r7} mm en 7 dies). "
                f"Suficient per a una eclosió puntual en microclimes humits, tot i que una pluja addicional consolidaria la producció."
            )
        else:
            rain_det = (
                f"Dèficit hídric: només {r14} mm en 14 dies. Està per sota del llindar recomanat de {species.rain_trigger_14d_min_mm} mm, "
                f"cosa que manté el miceli en estat de latència."
            )

        # Soil explanation
        soil_pct = factors.soil_moisture_pct
        if factors.soil_score >= 80:
            soil_det = f"Sòl en condicions òptimes d'hidratació ({soil_pct}%). Manté el mantell freàtic humit evitant que els primordis s'assequin."
        elif factors.soil_score >= 50:
            soil_det = f"Humitat superficial acceptable ({soil_pct}%). Favorable en fondalades i sota catifes de molsa."
        else:
            soil_det = f"Sòl ressec ({soil_pct}%). Risc elevat d'avortament dels bolets naixents per manca de reserva d'aigua."

        # Temperature explanation
        t_mean = factors.temp_mean_c
        t_min = factors.temp_min_c
        t_max = factors.temp_max_c
        opt_t_low, opt_t_high = species.optimal_temp_mean_c

        if factors.temp_score >= 80:
            temp_det = (
                f"Termòmetre ideal: mitjana de {t_mean}°C (mínima {t_min}°C, màxima {t_max}°C), "
                f"dins la finestra òptima de creixement ({opt_t_low}-{opt_t_high}°C) sense cap risc de glaçada destructiva."
            )
        elif factors.temp_score >= 50:
            temp_det = (
                f"Règim tèrmic acceptable ({t_mean}°C de mitjana). Mínimes nocturnes de {t_min}°C que alenteixen "
                f"lleugerament el creixement però mantenen la viabilitat."
            )
        else:
            if t_min <= 0.0 and species.frost_sensitivity in ["high", "extreme"]:
                temp_det = f"Glaçades recents detectades ({t_min}°C de mínima). El fred intens ha malmès els primordis d'aquesta espècie sensible."
            elif t_mean > opt_t_high:
                temp_det = f"Temperatures massa caloroses ({t_mean}°C de mitjana, màxima de {t_max}°C) que acceleren l'evaporació i assequen l'ambient."
            else:
                temp_det = f"Temperatures fredes ({t_mean}°C) allunyades del rang ideal ({opt_t_low}-{opt_t_high}°C)."

        # Habitat explanation
        if factors.habitat_score >= 85:
            hab_det = f"Hàbitat perfecte: la massa forestal de {forest} sobre sòl {zone.get('soil_type', 'favorable')} forma una simbiosi micorrízica òptima amb {species.name_ca}."
        elif factors.habitat_score >= 50:
            hab_det = f"Hàbitat compatible: {forest}. Presència possible d'arbres hoste en clapes mixtes."
        else:
            hab_det = f"Bosc poc favorable: {forest}. Aquesta espècie requereix típicament {', '.join(species.habitats[:2])}."

        # Aspect & Shading explanation
        if "Obaga" in aspect:
            aspect_det = (
                f"Orientació d'Obaga (Nord/Ombrívola) a {elev}m: Reté la humitat de les darreres pluges i redueix la insolació "
                f"dràsticament. Clau per evitar que el vent eixugui el sòl en èpoques temperades."
            )
        elif "Solana" in aspect:
            aspect_det = (
                f"Orientació de Solana (Sud/Assolellada) a {elev}m: Major radiació tèrmica. Favorable a la tardor avançada "
                f"per protegir-se de les glaçades o per a espècies termòfiles com l'ou de reig."
            )
        elif "Fons de vall" in aspect:
            aspect_det = (
                f"Fons de vall humit a {elev}m: Convergència d'escolament d'aigües i humitat constant, creant un microclima excepcional."
            )
        else:
            aspect_det = f"Topografia oberta a {elev}m d'altitud."

        # Global Summary (Catalan & English)
        if prob >= 85.0:
            summary_ca = f"Condicions EXCEL·LENTS a {z_name} (>85%). La combinació de pluges acumulades ({r14} mm), sòl humit ({soil_pct}%) i l'hàbitat idoni de {forest} fa molt probable trobar {species.name_ca}."
            summary_en = f"EXCELLENT conditions at {z_name} (>85%). Favorable rain ({r14} mm), damp soil ({soil_pct}%), and matching {forest} create peak fruiting potential for {species.name_ca}."
        elif prob >= 70.0:
            summary_ca = f"Bones condicions a {z_name} (~75%). El patró de precipitació i temperatura és favorable, especialment als sectors més protegits i humits."
            summary_en = f"Favorable conditions at {z_name} (~75%). Meteorological and environmental factors support mushroom fruiting, especially in sheltered spots."
        elif prob >= 55.0:
            summary_ca = f"Probabilitat moderada a {z_name}. Cal buscar en microhàbitats molt específics (fondalades, vores de rierols o sota catifes denses de molsa)."
            summary_en = f"Moderate probability at {z_name}. Best chances are restricted to specific micro-habitats (damp ravines, moss beds)."
        else:
            summary_ca = f"Baixa probabilitat actual a {z_name} (≤50%). La manca de pluja suficient o la incompatibilitat del bosc/altitud redueixen dràsticament l'eclosió."
            summary_en = f"Low probability at {z_name} (≤50%) currently due to insufficient rainfall or habitat mismatch."

        # Forager tips
        if species.id == "cep":
            tips = "Busqueu en pendents suaus amb fullaraca humida o sota mates de bruc i nabius, evitant llocs on el bestiar hagi trepitjat el terra."
        elif species.id == "rovello":
            tips = "Vigileu els marges dels camins, clarianes de pins joves i zones amb pedres calcaries on l'aigua s'acumula sense entollar-se."
        elif species.id == "camagroc":
            tips = "Mireu directament sobre la molsa espessa a les obagues fresques. Sovint estan camuflats i, en trobar-ne un, en teniu desenes al voltant!"
        elif species.id == "trompeta":
            tips = "Passeu la vista a poc a poc per les acumulacions de fulles de faig i roure. El color negre es confon fàcilment amb la terra fosca humida."
        elif species.id == "ou_de_reig":
            tips = "Cerqueu en alzinars i suredes assolellades després de tronades d'estiu o inici de tardor. No colliu mai exemplars massa tancats!"
        else:
            tips = "Porteu sempre cistell de vímet per escampar les espores i ganivet per tallar el peu sense arrencar el miceli."

        return ZoneExplanation(
            rating_ca=rating_ca,
            rating_en=rating_en,
            badge_color=badge_color,
            summary_ca=summary_ca,
            summary_en=summary_en,
            rain_detail=rain_det,
            soil_detail=soil_det,
            temp_detail=temp_det,
            habitat_detail=hab_det,
            aspect_detail=aspect_det,
            forager_tips=tips,
            toxicity_warning=species.toxicity_warning
        )
