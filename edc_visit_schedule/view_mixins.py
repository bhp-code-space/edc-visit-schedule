from edc_visit_schedule.site_visit_schedules import site_visit_schedules


class VisitScheduleViewMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._enrollment_models = []
        self.current_enrollment_model = None
        self.schedule = None
        self.visit_schedules = []

    def get(self, request, *args, **kwargs):
        kwargs['visit_schedules'] = self.visit_schedules
        kwargs['enrollment_models'] = self.enrollment_models
        kwargs['current_enrollment_model'] = self.current_enrollment_model
        return super().get(request, *args, **kwargs)

    @property
    def enrollment_models(self):
        """Returns a list of enrollment model instances.
        """
        if not self._enrollment_models:
            # find if the subject has an enrollment for for a schedule
            for visit_schedule in site_visit_schedules.get_visit_schedules().values():
                for schedule in visit_schedule.schedules.values():
                    enrollment_instance = schedule.enrollment_instance(
                        subject_identifier=self.subject_identifier)
                    if enrollment_instance:
                        self.visit_schedules.append(visit_schedule)
                        if self.is_current_enrollment_model(
                                enrollment_instance, schedule=schedule):
                            enrollment_instance.current = True
                            self.current_enrollment_model = enrollment_instance
                        self._enrollment_models.append(enrollment_instance)
                        break
        return self._enrollment_models

    def is_current_enrollment_model(self, enrollment_instance,
                                    visit_schedule=None, **kwargs):
        """Returns True if instance is the current enrollment model.

        Override to set the criteria of what is "current"
        """
        return False
