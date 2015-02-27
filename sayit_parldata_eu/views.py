from speeches.models import Section
from speeches.views import ParentlessList

class RecentView(ParentlessList):
    template_name = 'speeches/recent_view.html'

    def get_context_data(self, **kwargs):
        context = super(ParentlessList, self).get_context_data(**kwargs)

        qs = Section.objects.for_instance(self.request.instance)
        context['term_list'] = qs.filter(parent=None).order_by('-start_date', '-start_time')[:]
        if context['term_list']:
            current_term = context['term_list'][0]
            context['session_list'] = qs.filter(parent=current_term).order_by('-start_date', '-start_time')[:5]
            if context['session_list']:
                current_session = context['session_list'][0]
                context['sitting_list'] = qs.filter(parent=current_session).order_by('-start_date', '-start_time')
        return context
