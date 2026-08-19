"""Localization helpers for HA Inspector engine messages."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final

DEFAULT_LANGUAGE: Final = "en"
SUPPORTED_LANGUAGES: Final = ("en", "es")

if TYPE_CHECKING:
    from .models import Finding

_TRANSLATIONS: Final[dict[str, dict[str, str]]] = {
    "en": {
        "backup_age.too_old.title": "The newest backup is too old",
        "backup_age.becoming_old.title": "The newest backup is becoming old",
        "backup_age.description": (
            "The newest available Home Assistant backup is "
            "{age_days} days old."
        ),
        "backup_age.recommendation": (
            "Create a new backup and verify that scheduled backups "
            "are running correctly."
        ),
    },
    "es": {
        "backup_age.too_old.title": (
            "La copia de seguridad más reciente es demasiado antigua"
        ),
        "backup_age.becoming_old.title": (
            "La copia de seguridad más reciente empieza a ser antigua"
        ),
        "backup_age.description": (
            "La copia de seguridad más reciente de Home Assistant "
            "tiene {age_days} días."
        ),
        "backup_age.recommendation": (
            "Crea una nueva copia de seguridad y comprueba que las "
            "copias programadas se ejecutan correctamente."
        ),
    },
}


def normalize_language(language: str | None) -> str:
    """Return a supported base language code."""
    if not language:
        return DEFAULT_LANGUAGE

    normalized = language.strip().lower().replace("_", "-")
    base_language = normalized.split("-", 1)[0]

    if base_language in SUPPORTED_LANGUAGES:
        return base_language

    return DEFAULT_LANGUAGE


def translate(
    key: str,
    *,
    language: str | None = None,
    variables: Mapping[str, Any] | None = None,
) -> str:
    """Translate one engine message."""
    selected_language = normalize_language(language)

    text = _TRANSLATIONS.get(selected_language, {}).get(key)

    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)

    if variables:
        return text.format(**variables)

    return text


_FINDING_TRANSLATIONS: Final[
    dict[str, dict[str, dict[str, str]]]
] = {
    "es": {
        # Backups
        "BACKUP_COUNT_NONE": {
            "title": "No hay copias de seguridad disponibles",
            "description": (
                "Home Assistant no informa actualmente de ninguna "
                "copia de seguridad disponible."
            ),
            "recommendation": (
                "Crea una nueva copia de seguridad y conserva varias "
                "copias recientes, preferiblemente con al menos una "
                "fuera del dispositivo de Home Assistant."
            ),
        },
        "BACKUP_COUNT_LOW": {
            "title": "Hay pocas copias de seguridad disponibles",
            "description": (
                "Home Assistant informa de {backup_count} copias de "
                "seguridad disponibles; se recomiendan al menos "
                "{minimum_recommended}."
            ),
            "recommendation": (
                "Crea una nueva copia de seguridad y conserva varias "
                "copias recientes, preferiblemente con al menos una "
                "fuera del dispositivo de Home Assistant."
            ),
        },
        "BACKUP_AGE_CRITICAL": {
            "title": (
                "La copia de seguridad más reciente es demasiado antigua"
            ),
            "description": (
                "La copia de seguridad más reciente de Home Assistant "
                "tiene {backup_age_days} días."
            ),
            "recommendation": (
                "Crea una nueva copia de seguridad y comprueba que las "
                "copias programadas se ejecutan correctamente."
            ),
        },
        "BACKUP_AGE_HIGH": {
            "title": (
                "La copia de seguridad más reciente empieza a ser antigua"
            ),
            "description": (
                "La copia de seguridad más reciente de Home Assistant "
                "tiene {backup_age_days} días."
            ),
            "recommendation": (
                "Crea una nueva copia de seguridad y comprueba que las "
                "copias programadas se ejecutan correctamente."
            ),
        },
        "BACKUP_AGENT_ERRORS_FOUND": {
            "title": (
                "Se han detectado errores en agentes de copia de seguridad"
            ),
            "description": (
                "{agent_error_count} agentes de copia de seguridad "
                "han devuelto errores al leer el inventario de copias."
            ),
            "recommendation": (
                "Revisa los agentes afectados, sus credenciales y "
                "conectividad, y comprueba que las copias remotas "
                "siguen creándose correctamente."
            ),
        },
        "BACKUP_REDUNDANCY_LOW": {
            "title": (
                "La copia de seguridad más reciente no tiene "
                "redundancia suficiente"
            ),
            "description": (
                "La copia más reciente está disponible mediante "
                "{latest_backup_agent_count} agentes; se recomiendan "
                "al menos {minimum_recommended_agents}."
            ),
            "recommendation": (
                "Guarda la copia más reciente en al menos dos ubicaciones "
                "independientes, incluida una fuera del dispositivo "
                "de Home Assistant."
            ),
        },
        "BACKUP_INTEGRITY_INCOMPLETE": {
            "title": (
                "La copia de seguridad más reciente está incompleta"
            ),
            "description": (
                "Home Assistant informa de que uno o más componentes "
                "solicitados no pudieron incluirse en la copia más reciente."
            ),
            "recommendation": (
                "Revisa los componentes y agentes que han fallado, "
                "corrige los errores y crea una nueva copia antes de "
                "depender de este punto de recuperación."
            ),
        },
        "BACKUP_INTEGRITY_AGENT_FAILURES": {
            "title": (
                "La copia más reciente falló en algunos destinos "
                "de almacenamiento"
            ),
            "description": (
                "La copia se creó, pero Home Assistant informa de errores "
                "al escribirla en uno o más agentes de copia de seguridad."
            ),
            "recommendation": (
                "Revisa los componentes y agentes que han fallado, "
                "corrige los errores y crea una nueva copia antes de "
                "depender de este punto de recuperación."
            ),
        },

        # Storage
        "DISK_FREE_SPACE_CRITICAL": {
            "title": "El espacio libre en disco es críticamente bajo",
            "description": (
                "El almacenamiento de Home Assistant sólo dispone de "
                "{free_percent:.2f}% de espacio libre."
            ),
            "recommendation": (
                "Elimina copias antiguas y archivos innecesarios, reduce "
                "la retención de Recorder si procede o amplía el "
                "almacenamiento disponible."
            ),
        },
        "DISK_FREE_SPACE_LOW": {
            "title": "El espacio libre en disco es bajo",
            "description": (
                "El almacenamiento de Home Assistant sólo dispone de "
                "{free_percent:.2f}% de espacio libre."
            ),
            "recommendation": (
                "Elimina copias antiguas y archivos innecesarios, reduce "
                "la retención de Recorder si procede o amplía el "
                "almacenamiento disponible."
            ),
        },

        # Entities
        "UNAVAILABLE_ENTITIES_EXCESSIVE": {
            "title": "Hay demasiadas entidades no disponibles",
            "description": (
                "{unavailable_count} de {total_entities} entidades no "
                "están disponibles ({unavailable_percentage}%)."
            ),
            "recommendation": (
                "Revisa los dominios afectados e identifica dispositivos "
                "o servicios desconectados, apagados o que ya no se utilicen."
            ),
        },
        "UNAVAILABLE_ENTITIES_HIGH": {
            "title": "Hay varias entidades no disponibles",
            "description": (
                "{unavailable_count} de {total_entities} entidades no "
                "están disponibles ({unavailable_percentage}%)."
            ),
            "recommendation": (
                "Revisa los dominios afectados e identifica dispositivos "
                "o servicios desconectados, apagados o que ya no se utilicen."
            ),
        },
        "UNKNOWN_ENTITIES_EXCESSIVE": {
            "title": "Hay demasiadas entidades con estado desconocido",
            "description": (
                "{unknown_count} de {total_entities} entidades tienen "
                "estado desconocido ({unknown_percentage}%)."
            ),
            "recommendation": (
                "Revisa entidades de plantilla, ayudantes e integraciones "
                "que todavía no hayan recibido su primer valor válido."
            ),
        },
        "UNKNOWN_ENTITIES_HIGH": {
            "title": "Hay varias entidades con estado desconocido",
            "description": (
                "{unknown_count} de {total_entities} entidades tienen "
                "estado desconocido ({unknown_percentage}%)."
            ),
            "recommendation": (
                "Revisa entidades de plantilla, ayudantes e integraciones "
                "que todavía no hayan recibido su primer valor válido."
            ),
        },
        "DUPLICATE_ENTITY_NAMES_FOUND": {
            "title": "Se han detectado nombres de entidad duplicados",
            "description": (
                "{duplicate_count} nombres descriptivos son utilizados "
                "por varias entidades."
            ),
            "recommendation": (
                "Asigna nombres distintos a las entidades afectadas para "
                "que los paneles, automatizaciones y comandos de voz sean "
                "más fáciles de identificar."
            ),
        },
        "ENTITIES_WITHOUT_AREA_FOUND": {
            "title": "Hay entidades sin un área asignada",
            "description": (
                "{unassigned_area_count} entidades no tienen un área asignada."
            ),
            "recommendation": (
                "Asigna áreas cuando corresponda para mejorar los paneles, "
                "el control por voz y la organización de las entidades."
            ),
        },

        # Integrations
        "INTEGRATION_SETUP_ERRORS": {
            "title": "Hay integraciones que no pudieron iniciarse",
            "description": (
                "{count} entradas de configuración de integraciones "
                "fallaron durante el inicio."
            ),
            "recommendation": (
                "Abre Ajustes > Dispositivos y servicios, revisa las "
                "integraciones afectadas y consulta el registro de "
                "Home Assistant para localizar el error original."
            ),
        },
        "INTEGRATION_SETUP_RETRIES": {
            "title": "Hay integraciones esperando un nuevo intento",
            "description": (
                "{count} entradas de configuración no pudieron iniciarse "
                "y están esperando un reintento automático."
            ),
            "recommendation": (
                "Comprueba la conectividad, credenciales y dispositivos "
                "dependientes. Ejecuta HA Inspector de nuevo después del "
                "reintento de Home Assistant."
            ),
        },
        "INTEGRATION_LIFECYCLE_ERRORS": {
            "title": (
                "Se han detectado errores en el ciclo de vida "
                "de integraciones"
            ),
            "description": (
                "{count} entradas de configuración presentan errores "
                "de migración o descarga."
            ),
            "recommendation": (
                "Revisa las integraciones afectadas y el registro de "
                "Home Assistant. Puede ser necesario reiniciar después "
                "de corregir el error."
            ),
        },

        # Recorder
        "RECORDER_UNAVAILABLE": {
            "title": "Recorder no está disponible",
            "description": (
                "HA Inspector no ha podido acceder a la instancia de "
                "Recorder de Home Assistant."
            ),
            "recommendation": (
                "Comprueba que Recorder esté cargado y revisa el registro "
                "de Home Assistant en busca de errores."
            ),
        },
        "RECORDER_DATABASE_NOT_CONNECTED": {
            "title": "La base de datos de Recorder no está conectada",
            "description": (
                "Recorder está cargado, pero su conexión con la base "
                "de datos no está disponible actualmente."
            ),
            "recommendation": (
                "Revisa los errores de Recorder y de la base de datos "
                "en el registro de Home Assistant."
            ),
        },
        "RECORDER_DATABASE_NOT_READY": {
            "title": "La base de datos de Recorder aún no está preparada",
            "description": (
                "Recorder está conectado, pero la base de datos todavía "
                "no está preparada para el funcionamiento normal."
            ),
            "recommendation": (
                "Espera a que termine la inicialización o migración de "
                "la base de datos y vuelve a ejecutar la inspección."
            ),
        },
        "RECORDER_KEEP_DAYS_UNKNOWN": {
            "title": "Se desconoce el periodo de retención de Recorder",
            "description": (
                "HA Inspector no ha podido determinar durante cuántos "
                "días se conserva el historial de Recorder."
            ),
        },
        "RECORDER_KEEP_DAYS_EXCESSIVE": {
            "title": "La retención de Recorder es muy alta",
            "description": (
                "Recorder está configurado para conservar el historial "
                "detallado durante {keep_days} días."
            ),
            "recommendation": (
                "Considera reducir purge_keep_days salvo que este periodo "
                "sea intencionado y la base de datos disponga de espacio "
                "y rendimiento suficientes."
            ),
        },
        "RECORDER_KEEP_DAYS_HIGH": {
            "title": "La retención de Recorder es alta",
            "description": (
                "Recorder está configurado para conservar el historial "
                "detallado durante {keep_days} días."
            ),
            "recommendation": (
                "Comprueba si este periodo de retención es necesario. "
                "Una retención larga puede aumentar el tamaño de la base "
                "de datos y el tiempo de mantenimiento."
            ),
        },
        "RECORDER_DATABASE_SIZE_HIGH": {
            "title": "La base de datos de Recorder es grande",
            "description": (
                "La base de datos de Recorder supera el umbral recomendado "
                "de advertencia."
            ),
            "recommendation": (
                "Revisa la retención y las exclusiones de Recorder y "
                "supervisa el crecimiento de la base de datos."
            ),
        },
        "RECORDER_DATABASE_SIZE_EXCESSIVE": {
            "title": "La base de datos de Recorder es muy grande",
            "description": (
                "La base de datos de Recorder supera el umbral recomendado "
                "de error."
            ),
            "recommendation": (
                "Revisa la retención, las exclusiones y el crecimiento de "
                "la base de datos. Considera reducir purge_keep_days o "
                "excluir entidades de alta frecuencia si este tamaño no "
                "es intencionado."
            ),
        },

        # Network
        "DNS_RESOLUTION_FAILED": {
            "title": "La resolución DNS está fallando",
            "description": (
                "El host de Home Assistant no pudo resolver los nombres "
                "DNS públicos utilizados por HA Inspector."
            ),
            "recommendation": (
                "Comprueba los servidores DNS configurados, la puerta de "
                "enlace y la conectividad de red ascendente."
            ),
        },
        "HOST_INTERNET_UNAVAILABLE": {
            "title": "El host no tiene conectividad a Internet",
            "description": (
                "Home Assistant Supervisor informa de que el host no "
                "dispone actualmente de conectividad a Internet."
            ),
            "recommendation": (
                "Comprueba la interfaz de red del host, la puerta de "
                "enlace, la configuración DNS y la conexión del router."
            ),
        },
        "SUPERVISOR_INTERNET_UNAVAILABLE": {
            "title": "Supervisor no tiene conectividad a Internet",
            "description": (
                "El host tiene conectividad a Internet, pero Home "
                "Assistant Supervisor informa de que no puede acceder "
                "a Internet."
            ),
            "recommendation": (
                "Revisa la red de Supervisor, la configuración DNS y "
                "las reglas de firewall o proxy que afecten a Home "
                "Assistant."
            ),
        },

        # System log
        "SYSTEM_LOG_ERRORS": {
            "title": "Se encontraron errores recientes en el registro",
            "description": (
                "Se registraron {error_entries} entradas distintas de "
                "error y {critical_entries} entradas críticas recientemente."
            ),
            "recommendation": (
                "Revisa el registro del sistema de Home Assistant e "
                "investiga los loggers que aparecen con mayor frecuencia."
            ),
        },
        "SYSTEM_LOG_WARNINGS": {
            "title": "Se encontraron avisos recientes en el registro",
            "description": (
                "Se registraron {warning_entries} entradas distintas de "
                "aviso recientemente."
            ),
            "recommendation": (
                "Revisa el registro del sistema de Home Assistant y "
                "supervisa los avisos repetidos que puedan indicar un "
                "funcionamiento degradado."
            ),
        },

        # System
        "TIME_SYNCHRONIZATION_FAILED": {
            "title": "La hora del sistema no está sincronizada",
            "description": (
                "Home Assistant informa de que el reloj del host no está "
                "sincronizado actualmente."
            ),
            "recommendation": (
                "Comprueba la conectividad de red y la sincronización NTP "
                "del host de Home Assistant y verifica después que el reloj "
                "del sistema quede sincronizado."
            ),
        },
        "RESTART_FREQUENCY_HIGH": {
            "title": "Home Assistant se reinicia con frecuencia",
            "description": (
                "Home Assistant se ha reiniciado {restart_count_24h} veces "
                "durante las últimas 24 horas."
            ),
            "recommendation": (
                "Supervisa los siguientes reinicios y revisa el registro "
                "en busca de apagados, fallos o actividad del watchdog."
            ),
        },
        "RESTART_FREQUENCY_CRITICAL": {
            "title": "Home Assistant se reinicia con demasiada frecuencia",
            "description": (
                "Home Assistant se ha reiniciado {restart_count_24h} veces "
                "durante las últimas 24 horas."
            ),
            "recommendation": (
                "Revisa el registro de Home Assistant, actualizaciones "
                "recientes, fallos de integraciones y la estabilidad del "
                "sistema para localizar la causa."
            ),
        },
        "MEMORY_USAGE_HIGH": {
            "title": "El uso de memoria es alto",
            "description": (
                "El uso actual de memoria del host es del "
                "{memory_percent:.1f}%."
            ),
            "recommendation": (
                "Supervisa el uso de memoria y revisa integraciones o "
                "complementos exigentes si el consumo permanece alto."
            ),
        },
        "MEMORY_USAGE_CRITICAL": {
            "title": "El uso de memoria es críticamente alto",
            "description": (
                "El uso actual de memoria del host es del "
                "{memory_percent:.1f}%."
            ),
            "recommendation": (
                "Revisa integraciones, complementos y otros procesos que "
                "puedan estar consumiendo demasiada memoria."
            ),
        },
        "CPU_LOAD_HIGH": {
            "title": "El uso de CPU es alto",
            "description": (
                "El uso actual de CPU del host es del {cpu_percent:.1f}%."
            ),
            "recommendation": (
                "Supervisa el uso de CPU y revisa integraciones o "
                "automatizaciones exigentes si la carga permanece alta."
            ),
        },
        "CPU_LOAD_CRITICAL": {
            "title": "El uso de CPU es críticamente alto",
            "description": (
                "El uso actual de CPU del host es del {cpu_percent:.1f}%."
            ),
            "recommendation": (
                "Revisa integraciones activas, automatizaciones y otros "
                "procesos que puedan estar consumiendo demasiada CPU."
            ),
        },

        "SYSTEM_INFORMATION_UNAVAILABLE": {
            "title": "La información del sistema no está disponible",
            "description": (
                "HA Inspector no ha podido recopilar la información "
                "general del sistema."
            ),
            "recommendation": (
                "Revisa el registro de Home Assistant en busca de errores "
                "producidos por el recopilador del sistema."
            ),
        },
        "SYSTEM_INFORMATION": {
            "title": "Información del sistema recopilada",
            "description": (
                "HA Inspector ha recopilado correctamente información "
                "general sobre esta instalación de Home Assistant."
            ),
        },

        # Automations
        "DISABLED_AUTOMATIONS_FOUND": {
            "title": "Se han detectado automatizaciones deshabilitadas",
            "description": (
                "{disabled_automation_count} automatizaciones están "
                "deshabilitadas en el registro de entidades."
            ),
            "recommendation": (
                "Revísalas y vuelve a habilitar las que sigan siendo "
                "necesarias o elimina las entradas obsoletas."
            ),
        },
    },
}

def localize_finding(
    finding: Finding,
    language: str | None,
) -> Finding:
    """Return a localized copy of a finding."""
    from .models import Finding

    selected_language = normalize_language(language)

    if selected_language == DEFAULT_LANGUAGE:
        return finding

    messages = _FINDING_TRANSLATIONS.get(
        selected_language,
        {},
    ).get(finding.finding_id)

    if not messages:
        return finding

    def render(
        field: str,
        fallback: str | None,
    ) -> str | None:
        template = messages.get(field)

        if template is None:
            return fallback

        try:
            return template.format(**finding.data)
        except (KeyError, ValueError):
            return fallback

    return Finding(
        finding_id=finding.finding_id,
        severity=finding.severity,
        title=render("title", finding.title) or finding.title,
        description=(
            render("description", finding.description)
            or finding.description
        ),
        recommendation=render(
            "recommendation",
            finding.recommendation,
        ),
        documentation_url=finding.documentation_url,
        data=dict(finding.data),
    )
