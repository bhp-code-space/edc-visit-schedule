import re

from django.core.management.color import color_style

from .visit_collection import VisitCollection
from ..site_visit_schedules import site_visit_schedules, SiteVisitScheduleError
from ..subject_schedule import NotOnScheduleError, NotOnScheduleForDateError
from ..subject_schedule import SubjectSchedule, SubjectScheduleError
from ..visit import Visit

style = color_style()


class ScheduleError(Exception):
    pass


class ScheduleNameError(Exception):
    pass


class AlreadyRegisteredVisit(Exception):
    pass


class Schedule:
    """A class that represents a "schedule" of visits.

    Is contained by a "visit schedule".

    Contains an ordered dictionary of visit instances and the onschedule
    and offschedule models used to get on and off the schedule.
    """
    name_regex = r'[a-z0-9\_\-]+$'
    visit_cls = Visit
    visit_collection_cls = VisitCollection
    subject_schedule_cls = SubjectSchedule

    def __init__(self, name=None, verbose_name=None, sequence=None, onschedule_model=None,
                 offschedule_model=None, appointment_model=None, consent_model=None):
        self._subject = None
        self.visits = self.visit_collection_cls()
        if not name or not re.match(r'[a-z0-9\_\-]+$', name):
            raise ScheduleNameError(
                f'Invalid name. Got \'{name}\'. May only contains numbers, '
                'lower case letters and \'_\'.')
        else:
            self.name = name
        self.verbose_name = verbose_name or name
        self.sequence = sequence or name

        self.appointment_model = appointment_model.lower()
        self.consent_model = consent_model.lower()
        self.offschedule_model = offschedule_model.lower()
        self.onschedule_model = onschedule_model.lower()

    def check(self):
        warnings = []
        try:
            self.subject.check()
        except (SiteVisitScheduleError, SubjectScheduleError) as e:
            warnings.append(
                f'{e} See schedule \'{self.name}\'.')
        return warnings

    def __repr__(self):
        return f'Schedule({self.name})'

    def __str__(self):
        return self.name

    def add_visit(self, visit=None, **kwargs):
        """Adds a unique visit to the schedule.
        """
        visit = visit or self.visit_cls(**kwargs)
        for attr in ['code', 'title', 'timepoint', 'rbase']:
            if getattr(visit, attr) in [getattr(v, attr) for v in self.visits.values()]:
                raise AlreadyRegisteredVisit(
                    f'Visit already registered. Got visit={visit} ({attr}). '
                    f'See schedule \'{self}\'')
        self.visits.update({visit.code: visit})
        return visit

    @property
    def field_value(self):
        return self.name

    @property
    def subject(self):
        """Returns a SubjectSchedule instance.

        Note: SubjectSchedule puts a subject on to a schedule or takes a subject
        off of a schedule.
        """
        if not self._subject:
            visit_schedule, schedule = (
                site_visit_schedules.get_by_onschedule_model_schedule_name(
                    self.onschedule_model, name=self.name))
            if schedule.name != self.name:
                raise ValueError(
                    f'Site visit schedules return the wrong schedule object. '
                    f'Expected {repr(self)} for onschedule_mo'
                    f'del={self.onschedule_model}. '
                    f'Got {repr(schedule)}.')
            self._subject = self.subject_schedule_cls(
                visit_schedule=visit_schedule, schedule=self)
        return self._subject

    def put_on_schedule(self, onschedule_model_obj=None, base_appt_datetime=None,
                        subject_identifier=None, onschedule_datetime=None,
                        schedule_name=None):
        """Wrapper method to puts a subject onto this schedule.
        """
        self.subject.put_on_schedule(
            onschedule_model_obj=onschedule_model_obj,
            subject_identifier=subject_identifier,
            onschedule_datetime=onschedule_datetime,
            base_appt_datetime=base_appt_datetime,
            schedule_name=schedule_name)

    def refresh_schedule(self, subject_identifier=None, schedule_name=None):
        """Resaves the onschedule model to, for example, refresh
        appointments.
        """
        self.subject.resave(subject_identifier=subject_identifier,
                            schedule_name=schedule_name)

    def take_off_schedule(self, offschedule_model_obj=None, offschedule_datetime=None,
                          subject_identifier=None, schedule_name=None):
        self.subject.take_off_schedule(
            offschedule_model_obj=offschedule_model_obj,
            subject_identifier=subject_identifier,
            offschedule_datetime=offschedule_datetime,
            schedule_name=schedule_name)

    def is_onschedule(self, subject_identifier=None, report_datetime=None):
        try:
            self.subject.onschedule_or_raise(
                subject_identifier=subject_identifier,
                report_datetime=report_datetime)
        except (NotOnScheduleError, NotOnScheduleForDateError):
            return False
        return True

    @property
    def onschedule_model_cls(self):
        return self.subject.onschedule_model_cls

    @property
    def offschedule_model_cls(self):
        return self.subject.offschedule_model_cls

    @property
    def history_model_cls(self):
        return self.subject.history_model_cls

    @property
    def appointment_model_cls(self):
        return self.subject.appointment_model_cls

    @property
    def visit_model_cls(self):
        return self.subject.visit_model_cls
