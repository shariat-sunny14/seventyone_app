from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from module_setup.models import module_type, module_list, feature_list
from user_setup.models import access_list
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


def nav_barItemContext(request):
    if request.path.startswith('/admin/') or request.path.startswith('/accounts/login/'):
        return {}

    grouped_data = {}

    if request.user.is_authenticated:
        active_modules = module_list.objects.filter(is_active=True)
        active_types = module_type.objects.filter(is_active=True)

        access_list_data = access_list.objects.filter(user_id=request.user)

        for access_item in access_list_data:
            module_id = access_item.feature_id.module_id.module_id
            module_name = access_item.feature_id.module_id.module_name
            type_name = access_item.feature_id.type_id.type_name

            if module_id in active_modules.values_list('module_id', flat=True):
                if module_id not in grouped_data:
                    grouped_data[module_id] = {
                        'module_name': module_name,
                        'types': {},
                    }

                if type_name in active_types.filter(module_id=module_id).values_list('type_name', flat=True):
                    if type_name not in grouped_data[module_id]['types']:
                        grouped_data[module_id]['types'][type_name] = {
                            'type_icon': access_item.feature_id.type_id.type_icon,
                            'features': [],
                        }

                    # Check if the feature is active and has feature_type="Form"
                    if (access_item.feature_id.is_active and access_item.feature_id.feature_type == "Form"):
                        
                        grouped_data[module_id]['types'][type_name]['features'].append({
                            'feature_page_link': access_item.feature_id.feature_page_link,
                            'feature_icon': access_item.feature_id.feature_icon,
                            'feature_name': access_item.feature_id.feature_name,
                        })

    return {'grouped_data': grouped_data}


def get_user_org_details(request):
    org_name = None
    org_address = None
    if request.user.is_authenticated:
        user = request.user
        if user.org_id:
            try:
                org = organizationlst.objects.get(org_id=user.org_id)
                org_name = org.org_name
                org_address = org.address
            except organizationlst.DoesNotExist:
                pass
    return {'user_org_name': org_name, 'user_org_address': org_address}
