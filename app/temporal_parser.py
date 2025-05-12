"""
Temporal query parser for extracting date references from natural language text.

This module helps parse natural language date references like:
- "last week"
- "yesterday"
- "between March and April"
- "two months ago"
- "show me entries from last summer"
"""

import re
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TemporalParser:
    """Parse natural language date references into structured date filters."""

    def __init__(self):
        # Current date for relative references
        self.today = datetime.now().date()
        self.current_year = self.today.year
        self.current_month = self.today.month

        # Patterns for date extraction
        self.relative_date_patterns = [
            # Yesterday, today, tomorrow
            (r"\b(yesterday|today|tomorrow)\b", self._parse_day_reference),
            # Last/next n days/weeks/months/years
            (
                r"\b(last|past|previous|next|coming) (\d+) "
                r"(days?|weeks?|months?|years?)\b",
                self._parse_relative_timespan,
            ),
            # Last/next day/week/month/year
            (
                r"\b(last|past|previous|next|coming) "
                r"(day|week|month|year|summer|spring|fall|winter)\b",
                self._parse_relative_period,
            ),
            # N days/weeks/months/years ago
            (r"\b(\d+) (days?|weeks?|months?|years?) ago\b", self._parse_ago_timespan),
            # This day/week/month/year
            (r"\b(this) (day|week|month|year)\b", self._parse_this_period),
            # Between date and date
            (
                r"\b(between|from) (.*?) (and|to) (.*?)\b(?=\.|\s|$)",
                self._parse_date_range,
            ),
            # Since date
            (r"\bsince ([^\.]+)\b(?=\.|\s|$)", self._parse_since_date),
            # Before/after date
            (
                r"\b(before|after|until|till) ([^\.]+)\b(?=\.|\s|$)",
                self._parse_before_after_date,
            ),
            # Month name references
            (
                r"\b(january|february|march|april|may|june|july|august|"
                r"september|october|november|december)( \d{4})?\b",
                self._parse_month_reference,
            ),
            # Season references
            (
                r"\b(summer|spring|fall|autumn|winter)( \d{4})?\b",
                self._parse_season_reference,
            ),
            # Year references
            (r"\bin (\d{4})\b", self._parse_year_reference),
        ]

        # Month name to number mapping
        self.month_to_num = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sep": 9,
            "sept": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }

        # Season to month ranges mapping
        self.season_to_months = {
            "winter": (12, 2),  # December to February
            "spring": (3, 5),  # March to May
            "summer": (6, 8),  # June to August
            "fall": (9, 11),  # September to November
            "autumn": (9, 11),  # Same as fall
        }

    def parse_temporal_query(self, text: str) -> Optional[Dict[str, datetime]]:
        """
        Parse natural language text to extract date references.

        Args:
            text: The text to parse for date references

        Returns:
            Dictionary with date_from and/or date_to, or None if no dates found
        """
        if not text:
            return None

        text = text.lower()

        # Try each pattern until we find a match
        for pattern, handler in self.relative_date_patterns:
            matches = re.search(pattern, text)
            if matches:
                try:
                    result = handler(matches)
                    if result:
                        return result
                except Exception as e:
                    logger.error(
                        "Error parsing temporal reference "
                        f"'{matches.group(0)}': {str(e)}"
                    )

        # Check for explicit date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
        explicit_date = self._extract_explicit_date(text)
        if explicit_date:
            return explicit_date

        return None

    def _parse_day_reference(self, match: re.Match) -> Dict[str, datetime]:
        """Parse yesterday/today/tomorrow references."""
        reference = match.group(1)

        if reference == "yesterday":
            target_date = self.today - timedelta(days=1)
        elif reference == "today":
            target_date = self.today
        elif reference == "tomorrow":
            target_date = self.today + timedelta(days=1)
        else:
            return None

        # Return the full day range
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_relative_timespan(self, match: re.Match) -> Dict[str, datetime]:
        """Parse 'last X days/weeks/months/years' type references."""
        direction = match.group(1)
        count = int(match.group(2))
        unit = match.group(3).rstrip("s")  # Remove plural 's' if present

        if direction in ("last", "past", "previous"):
            if unit == "day":
                end_date = self.today
                start_date = end_date - timedelta(days=count)
            elif unit == "week":
                end_date = self.today
                start_date = end_date - timedelta(weeks=count)
            elif unit == "month":
                end_date = self.today
                # Approximate months as 30 days
                start_date = end_date - timedelta(days=30 * count)
            elif unit == "year":
                end_date = self.today
                # Approximate years as 365 days
                start_date = end_date - timedelta(days=365 * count)
        else:  # next, coming
            if unit == "day":
                start_date = self.today
                end_date = start_date + timedelta(days=count)
            elif unit == "week":
                start_date = self.today
                end_date = start_date + timedelta(weeks=count)
            elif unit == "month":
                start_date = self.today
                # Approximate months as 30 days
                end_date = start_date + timedelta(days=30 * count)
            elif unit == "year":
                start_date = self.today
                # Approximate years as 365 days
                end_date = start_date + timedelta(days=365 * count)

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_relative_period(self, match: re.Match) -> Dict[str, datetime]:
        """Parse 'last week/month/year' type references."""
        direction = match.group(1)
        unit = match.group(2)

        if direction in ("last", "past", "previous"):
            if unit == "day":
                target_date = self.today - timedelta(days=1)
                start_date = target_date
                end_date = target_date
            elif unit == "week":
                # Last week = 7-14 days ago
                end_date = self.today - timedelta(days=7)
                start_date = end_date - timedelta(days=6)
            elif unit == "month":
                # Last month = previous calendar month
                if self.current_month == 1:  # January
                    month = 12  # December
                    year = self.current_year - 1
                else:
                    month = self.current_month - 1
                    year = self.current_year

                start_date = date(year, month, 1)
                if month == 12:
                    end_month, end_year = 1, year + 1
                else:
                    end_month, end_year = month + 1, year

                end_date = date(end_year, end_month, 1) - timedelta(days=1)
            elif unit == "year":
                # Last year = previous calendar year
                start_date = date(self.current_year - 1, 1, 1)
                end_date = date(self.current_year - 1, 12, 31)
            elif unit in ("summer", "spring", "fall", "winter"):
                return self._parse_season_reference(match)
        else:  # next, coming
            if unit == "day":
                target_date = self.today + timedelta(days=1)
                start_date = target_date
                end_date = target_date
            elif unit == "week":
                # Next week = 7-14 days from now
                start_date = self.today + timedelta(days=7)
                end_date = start_date + timedelta(days=6)
            elif unit == "month":
                # Next month = next calendar month
                if self.current_month == 12:  # December
                    month = 1  # January
                    year = self.current_year + 1
                else:
                    month = self.current_month + 1
                    year = self.current_year

                start_date = date(year, month, 1)
                if month == 12:
                    end_month, end_year = 1, year + 1
                else:
                    end_month, end_year = month + 1, year

                end_date = date(end_year, end_month, 1) - timedelta(days=1)
            elif unit == "year":
                # Next year = next calendar year
                start_date = date(self.current_year + 1, 1, 1)
                end_date = date(self.current_year + 1, 12, 31)
            elif unit in ("summer", "spring", "fall", "winter"):
                return self._parse_season_reference(match)

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_ago_timespan(self, match: re.Match) -> Dict[str, datetime]:
        """Parse 'X days/weeks/months/years ago' references."""
        count = int(match.group(1))
        unit = match.group(2).rstrip("s")  # Remove plural 's' if present

        if unit == "day":
            target_date = self.today - timedelta(days=count)
        elif unit == "week":
            target_date = self.today - timedelta(weeks=count)
        elif unit == "month":
            # Approximate months as 30 days
            target_date = self.today - timedelta(days=30 * count)
        elif unit == "year":
            # Approximate years as 365 days
            target_date = self.today - timedelta(days=365 * count)

        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_this_period(self, match: re.Match) -> Dict[str, datetime]:
        """Parse 'this week/month/year' references."""
        unit = match.group(2)

        if unit == "day":
            start_date = self.today
            end_date = start_date
        elif unit == "week":
            # Get the start of this week (Sunday/Monday based on locale)
            today_weekday = self.today.weekday()  # 0 = Monday, 6 = Sunday
            days_since_start = today_weekday
            start_date = self.today - timedelta(days=days_since_start)
            end_date = start_date + timedelta(days=6)
        elif unit == "month":
            # This month = current calendar month
            start_date = date(self.current_year, self.current_month, 1)
            if self.current_month == 12:
                end_month, end_year = 1, self.current_year + 1
            else:
                end_month, end_year = self.current_month + 1, self.current_year

            end_date = date(end_year, end_month, 1) - timedelta(days=1)
        elif unit == "year":
            # This year = current calendar year
            start_date = date(self.current_year, 1, 1)
            end_date = date(self.current_year, 12, 31)

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_date_range(self, match: re.Match) -> Optional[Dict[str, datetime]]:
        """Parse 'between X and Y' or 'from X to Y' references."""
        from_ref = match.group(2).strip()
        to_ref = match.group(4).strip()

        # Try to parse each date reference
        from_date = self._parse_date_reference(from_ref)
        to_date = self._parse_date_reference(to_ref)

        if from_date and to_date:
            return {"date_from": from_date[0], "date_to": to_date[1]}

        return None

    def _parse_since_date(self, match: re.Match) -> Optional[Dict[str, datetime]]:
        """Parse 'since X' references."""
        date_ref = match.group(1).strip()

        parsed_date = self._parse_date_reference(date_ref)
        if parsed_date:
            now = datetime.combine(self.today, datetime.max.time())
            return {"date_from": parsed_date[0], "date_to": now}

        return None

    def _parse_before_after_date(
        self, match: re.Match
    ) -> Optional[Dict[str, datetime]]:
        """Parse 'before X' or 'after X' references."""
        direction = match.group(1)
        date_ref = match.group(2).strip()

        parsed_date = self._parse_date_reference(date_ref)
        if not parsed_date:
            return None

        if direction in ("before", "until", "till"):
            return {"date_to": parsed_date[0]}
        elif direction == "after":
            return {"date_from": parsed_date[1]}

        return None

    def _parse_month_reference(self, match: re.Match) -> Dict[str, datetime]:
        """Parse month name references."""
        month_name = match.group(1).lower()
        year_str = match.group(2).strip() if match.group(2) else None

        try:
            month_num = self.month_to_num.get(month_name)
            if not month_num:
                return None

            # Determine year - if specified or current year
            if year_str:
                year = int(year_str)
            else:
                # If we're past the referenced month this year, assume next year
                if month_num < self.current_month:
                    year = self.current_year + 1
                else:
                    year = self.current_year

            # Create date range for the entire month
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_month, end_year = 1, year + 1
            else:
                end_month, end_year = month_num + 1, year

            end_date = date(end_year, end_month, 1) - timedelta(days=1)

            start = datetime.combine(start_date, datetime.min.time())
            end = datetime.combine(end_date, datetime.max.time())
            return {"date_from": start, "date_to": end}
        except Exception as e:
            logger.error(f"Error parsing month reference: {str(e)}")
            return None

    def _parse_season_reference(self, match: re.Match) -> Dict[str, datetime]:
        """Parse season references (summer, winter, etc.)."""
        season_name = None
        year_str = None
        direction = None

        # Handle both direct season mentions and "last/next season" patterns
        if match.lastindex >= 2:
            if match.group(1) in ("summer", "spring", "fall", "autumn", "winter"):
                season_name = match.group(1).lower()
                year_str = match.group(2).strip() if match.group(2) else None
            else:
                direction = match.group(1).lower()
                season_name = match.group(2).lower()

        if not season_name or season_name not in self.season_to_months:
            return None

        start_month, end_month = self.season_to_months[season_name]

        # Determine year
        year = self.current_year
        if year_str:
            year = int(year_str)
        elif direction:
            if direction in ("last", "past", "previous"):
                year = self.current_year - 1
            elif direction in ("next", "coming"):
                year = self.current_year + 1

        # Handle winter which spans year boundary
        if season_name == "winter":
            if start_month > end_month:  # Dec to Feb
                # Winter starts in the specified year and ends in the next
                start_date = date(year, start_month, 1)
                end_date = date(year + 1, end_month + 1, 1) - timedelta(days=1)
            else:
                start_date = date(year, start_month, 1)
                end_date = date(year, end_month + 1, 1) - timedelta(days=1)
        else:
            start_date = date(year, start_month, 1)
            end_date = date(year, end_month + 1, 1) - timedelta(days=1)

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _parse_year_reference(self, match: re.Match) -> Dict[str, datetime]:
        """Parse year references."""
        year = int(match.group(1))

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        return {"date_from": start, "date_to": end}

    def _extract_explicit_date(self, text: str) -> Optional[Dict[str, datetime]]:
        """Extract explicit date formats from text."""
        # ISO format: YYYY-MM-DD
        iso_pattern = r"\b(\d{4}-\d{1,2}-\d{1,2})\b"
        # US format: MM/DD/YYYY or MM-DD-YYYY
        us_pattern = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b"
        # Short format: DD/MM/YY or DD-MM-YY
        short_pattern = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b"

        # Try ISO format first
        iso_matches = re.findall(iso_pattern, text)
        if iso_matches:
            try:
                date_obj = datetime.strptime(iso_matches[0], "%Y-%m-%d").date()
                return self._create_full_day_range(date_obj)
            except ValueError:
                pass

        # Try US format
        us_matches = re.findall(us_pattern, text)
        if us_matches:
            for format_str in ("%m/%d/%Y", "%m-%d-%Y"):
                try:
                    date_obj = datetime.strptime(us_matches[0], format_str).date()
                    return self._create_full_day_range(date_obj)
                except ValueError:
                    continue

        # Try short format
        short_matches = re.findall(short_pattern, text)
        if short_matches:
            for format_str in ("%d/%m/%y", "%d-%m-%y"):
                try:
                    date_obj = datetime.strptime(short_matches[0], format_str).date()
                    return self._create_full_day_range(date_obj)
                except ValueError:
                    continue

        return None

    def _parse_date_reference(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse a date reference string into a start/end datetime tuple.

        Args:
            text: Date reference string

        Returns:
            Tuple of (start_datetime, end_datetime) or None if parsing fails
        """
        # Try to parse as a day reference
        day_match = re.search(r"\b(yesterday|today|tomorrow)\b", text)
        if day_match:
            result = self._parse_day_reference(day_match)
            if result:
                return result["date_from"], result["date_to"]

        # Try to parse as a month
        month_match = re.search(
            r"\b(january|february|march|april|may|june|july|august|"
            r"september|october|november|december)( \d{4})?\b",
            text,
        )
        if month_match:
            result = self._parse_month_reference(month_match)
            if result:
                return result["date_from"], result["date_to"]

        # Try to parse as an explicit date
        filtered_text = f" {text} "  # Add spaces to help with word boundary matching
        date_filter = self._extract_explicit_date(filtered_text)
        if date_filter:
            return date_filter["date_from"], date_filter["date_to"]

        # Could not parse the reference
        return None

    def _create_full_day_range(self, date_obj: date) -> Dict[str, datetime]:
        """Create a datetime range covering a full day."""
        start = datetime.combine(date_obj, datetime.min.time())
        end = datetime.combine(date_obj, datetime.max.time())
        return {"date_from": start, "date_to": end}
