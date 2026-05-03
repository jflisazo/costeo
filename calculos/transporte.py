from models.recursos import CicloTransporte


def calc_ciclo_transporte(t: CicloTransporte, costo_hora_equipo: float) -> CicloTransporte:
    """
    Tiempo ciclo (minutos):
        t_ida  = distancia / vel_ida * 60
        t_vuelta = distancia / vel_vuelta * 60
        t_ciclo = t_ida + t_vuelta + espera + carga + descarga

    Rendimiento/día:
        viajes_por_dia = hs_dia * 60 / t_ciclo
        rend_dia = viajes_por_dia * capacidad

    Costo por unidad:
        costo = costo_hora_equipo / rend_dia   (si rend_dia > 0)
    """
    if t.vel_ida <= 0 or t.vel_vuelta <= 0:
        return t

    t_ida = t.distancia_km / t.vel_ida * 60
    t_vuelta = t.distancia_km / t.vel_vuelta * 60
    t_ciclo = t_ida + t_vuelta + t.tiempo_espera + t.tiempo_carga + t.tiempo_descarga

    if t_ciclo <= 0:
        return t

    viajes = t.hs_dia * 60 / t_ciclo
    rend_dia = viajes * t.capacidad

    costo = costo_hora_equipo * t.hs_dia / rend_dia if rend_dia > 0 else 0.0

    # Camiones necesarios para cubrir rendimiento_base
    n_camiones = t.rendimiento_base / rend_dia if rend_dia > 0 else 0.0

    return t.model_copy(update={
        "tiempo_viaje_min": round(t_ida + t_vuelta, 2),
        "tiempo_ciclo_min": round(t_ciclo, 2),
        "rend_dia": round(rend_dia, 4),
        "n_camiones": round(n_camiones, 2),
        "costo": round(costo, 4),
    })
