from django.contrib.gis.geos import LineString
from django.forms import ModelForm
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from django_countries.fields import Country

from maps import COUNTRIES_WITH_MANDATORY_REGION, SRID


class WhereaboutsAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self['bbox'].initial is not None:
            (minx, miny), (maxx, maxy) = self['bbox'].initial.coords
            self['bbox'].initial = LineString(
                (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny),
                srid=SRID
            )

    def clean_name(self):
        return self.cleaned_data['name'].upper()

    def clean_state(self):
        return self.cleaned_data['state'].upper()

    def clean_bbox(self):
        minx, miny, maxx, maxy = self.cleaned_data['bbox'].extent
        return LineString((minx, miny), (maxx, maxy), srid=SRID)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('country') in COUNTRIES_WITH_MANDATORY_REGION and not cleaned_data.get('state'):
            # Verifies that the region is indeed indicated when it is mandatory.
            message = _("For an address in {country}, the name of the state or province must be indicated.")
            self.add_error('state', format_lazy(message, country=Country(cleaned_data['country']).name))
        return cleaned_data

    def save(self, commit=True):
        location = super().save(commit=False)
        if 'bbox' in self.changed_data:
            location.center = location.bbox.centroid
        if commit:
            location.save()
        return location
