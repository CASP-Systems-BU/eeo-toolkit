from enum import Enum

class TableType(Enum):
    NAICS_AND_GENDER = "naics_and_gender"
    NAICS_AND_RACE = "naics_and_race"
    GENDER_AND_RACE = "gender_and_race"
    GENDER_AND_JOB = "gender_and_job"
    RACE_AND_JOB = "race_and_job"
    NAICS_AND_JOB = "naics_and_job"
    GENDER_RACE_JOB = "gender_race_job"


class YearType(Enum):
    CURRENT = "current_year_total"
    LAST = "last_year_total"
