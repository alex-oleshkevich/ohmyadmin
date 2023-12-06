from ohmyadmin.views.form import FormView
from ohmyadmin.views.resource import ResourceView
from ohmyadmin.views.table import TableView


class CountriesTable(TableView):
    label = "Countries"


class EditCountryView(FormView):
    label = "Edit Country"
    create_label = "Create country"


class CountriesResource(ResourceView):
    index_view = CountriesTable
    form_view = EditCountryView
    create_form_view = EditCountryView
