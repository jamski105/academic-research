"""
BookFetcherRouter -- testbarer Python-Spiegel der Routing-Logik aus agents/book-fetcher.md.

Dieser Modul implementiert dieselbe Routing-Logik, die der Agent-Prompt beschreibt,
damit wir sie mit unittest.mock testen koennen ohne echte Subagenten aufzurufen.
"""
import re
import datetime


# Subagent-Reihenfolgen (aus L0-Notes und Spec G.md)
OA_SUBAGENTS = ["doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"]

PUBLISHER_DOMAIN_MAP = {
    "link.springer.com": "springer-book",
    "degruyter.com": "degruyter",
    "nationallizenzen.de": "nationallizenzen",
    "ebookcentral.proquest.com": "ebook-central",
}


class BookFetcherRouter:
    """
    Simuliert die Routing-Logik des book-fetcher Master-Agenten.

    dispatch_subagent() kann in Tests gepatch werden, um echte Subagenten-
    Aufrufe zu simulieren.
    """

    def __init__(self, profile: dict):
        """
        Args:
            profile: Geparste active.yaml (dict mit licensed_sites, bib_pickup_url etc.)
        """
        self.profile = profile
        self.licensed_sites = set(profile.get("licensed_sites", []))
        self.bib_pickup_url = profile.get("bib_pickup_url", "")

    # ------------------------------------------------------------------
    # Input Parsing
    # ------------------------------------------------------------------

    def parse_input(self, raw: str) -> tuple:
        """
        Erkennt den Eingabe-Typ und gibt (typ, normalisierter_wert) zurueck.

        Typen: 'isbn', 'doi', 'url', 'title'
        """
        text = raw.strip()

        # Explizites 'isbn:'-Prefix
        if text.lower().startswith("isbn:"):
            val = text[5:].strip()
            return ("isbn", val)

        # URL
        if text.startswith("http://") or text.startswith("https://"):
            return ("url", text)

        # DOI (beginnt mit 10.)
        if re.match(r"10\.\d{4,}/", text):
            return ("doi", text)

        # ISBN-13: 13 Ziffern (mit oder ohne Bindestriche/Leerzeichen), beginnt mit 978 oder 979
        digits_only = re.sub(r"[- ]", "", text)
        if re.match(r"^97[89]\d{10}$", digits_only):
            return ("isbn", text)

        # ISBN-10: 10 Ziffern (letztes Zeichen darf X sein), mit oder ohne Bindestriche
        if re.match(r"^\d{9}[\dX]$", digits_only):
            return ("isbn", text)

        # Freitext / Titel
        return ("title", text)

    # ------------------------------------------------------------------
    # Subagent Dispatch (real implementation uses Agent(...) tool)
    # ------------------------------------------------------------------

    def dispatch_subagent(self, subagent_name: str, payload: dict) -> dict:
        """
        Wird in Tests durch unittest.mock.patch.object ersetzt.
        In Produktion wuerde der Agent-Prompt hier Agent(...) aufrufen.
        """
        raise NotImplementedError(
            "dispatch_subagent must be patched in tests or overridden for production"
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _ts(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    def _try_entry(self, subagent: str, status: str) -> dict:
        return {"subagent": subagent, "status": status, "ts": self._ts()}

    def fetch(self, identifier_raw: str, output_path: str) -> dict:
        """
        Haupt-Routing-Funktion. Gibt das Master-Output-Schema zurueck.

        Args:
            identifier_raw: Rohe Eingabe (ISBN, DOI, URL oder Titel)
            output_path: Zielpfad fuer die heruntergeladene PDF-Datei

        Returns:
            dict mit Keys: status, source, file_path?, reason?, tries, pickup_hint?
        """
        id_type, id_value = self.parse_input(identifier_raw)
        payload_base = {
            "output_path": output_path,
            id_type: id_value,
        }
        tries = []
        best_metadata_url = None  # Beste bekannte URL aus metadata_only-Responses

        # ----------------------------------------------------------
        # Schritt 1: OA-Subagenten
        # ----------------------------------------------------------
        oa_any_metadata_only = False
        for subagent in OA_SUBAGENTS:
            resp = self.dispatch_subagent(subagent, payload_base)
            status = resp.get("status", "no_match")
            tries.append(self._try_entry(subagent, status))

            if status == "success":
                return {
                    "status": "success",
                    "source": subagent,
                    "file_path": resp.get("pdf_path"),
                    "tries": tries,
                }

            if status == "captcha":
                return {
                    "status": "captcha",
                    "source": subagent,
                    "reason": resp.get("reason", "CAPTCHA erkannt"),
                    "tries": tries,
                }

            if status == "metadata_only":
                oa_any_metadata_only = True
                if resp.get("url") and not best_metadata_url:
                    best_metadata_url = resp["url"]

        # ----------------------------------------------------------
        # Schritt 2: Verlags-Subagenten (nur wenn OA metadata_only und lizenziert)
        # ----------------------------------------------------------
        if oa_any_metadata_only:
            publisher_subagents = self._get_licensed_publisher_subagents()
            for pub_subagent in publisher_subagents:
                result = self._try_publisher(pub_subagent, payload_base, tries)
                if result is not None:
                    return result

        # ----------------------------------------------------------
        # Schritt 3: Fallback generic-fetcher
        # ----------------------------------------------------------
        generic_payload = dict(payload_base)
        if best_metadata_url:
            generic_payload["url"] = best_metadata_url

        resp = self.dispatch_subagent("generic-fetcher", generic_payload)
        status = resp.get("status", "no_match")
        tries.append(self._try_entry("generic-fetcher", status))

        if status == "success":
            return {
                "status": "success",
                "source": "generic-fetcher",
                "file_path": resp.get("pdf_path"),
                "tries": tries,
            }

        if status == "captcha":
            return {
                "status": "captcha",
                "source": "generic-fetcher",
                "reason": resp.get("reason", "CAPTCHA erkannt"),
                "tries": tries,
            }

        # pickup_required oder no_match -- immer pickup_required mit Hinweis
        return {
            "status": "pickup_required",
            "source": "generic-fetcher",
            "reason": resp.get("reason", "Keine downloadbare Quelle gefunden"),
            "tries": tries,
            "pickup_hint": {
                "bib_pickup_url": self.bib_pickup_url,
                "identifier": id_value,
                "identifier_type": id_type,
            },
        }

    def _get_licensed_publisher_subagents(self) -> list:
        """Gibt die Verlags-Subagenten zurueck, deren Host in licensed_sites ist."""
        result = []
        for domain, subagent in PUBLISHER_DOMAIN_MAP.items():
            if domain in self.licensed_sites:
                result.append(subagent)
        return result

    def _try_publisher(self, pub_subagent: str, payload_base: dict,
                       tries: list):
        """
        Versucht einen Verlags-Subagenten. Handhabt auth_required mit auth-helper-Retry.

        Gibt das finale Ergebnis zurueck wenn erfolgreich/captcha, sonst None.
        """
        resp = self.dispatch_subagent(pub_subagent, payload_base)
        status = resp.get("status", "no_match")
        tries.append(self._try_entry(pub_subagent, status))

        if status == "success":
            return {
                "status": "success",
                "source": pub_subagent,
                "file_path": resp.get("pdf_path"),
                "tries": tries,
            }

        if status == "captcha":
            return {
                "status": "captcha",
                "source": pub_subagent,
                "reason": resp.get("reason", "CAPTCHA erkannt"),
                "tries": tries,
            }

        if status == "auth_required":
            # Auth-Helper aufrufen
            target_url = resp.get("url", "")
            auth_resp = self.dispatch_subagent("auth-helper", {
                "target_url": target_url,
                "profile_path": "~/.academic-research/library-profiles/active.yaml",
            })
            auth_status = auth_resp.get("status", "auth_failed")
            tries.append(self._try_entry("auth-helper", auth_status))

            if auth_status == "captcha":
                return {
                    "status": "captcha",
                    "source": "auth-helper",
                    "reason": "CAPTCHA beim Login",
                    "tries": tries,
                }

            if auth_status == "authenticated":
                # Einmaliger Retry
                retry_resp = self.dispatch_subagent(pub_subagent, payload_base)
                retry_status = retry_resp.get("status", "no_match")
                tries.append(self._try_entry(pub_subagent, retry_status))

                if retry_status == "success":
                    return {
                        "status": "success",
                        "source": pub_subagent,
                        "file_path": retry_resp.get("pdf_path"),
                        "tries": tries,
                    }

                if retry_status == "captcha":
                    return {
                        "status": "captcha",
                        "source": pub_subagent,
                        "reason": "CAPTCHA nach Auth-Retry",
                        "tries": tries,
                    }

            return None

        return None
