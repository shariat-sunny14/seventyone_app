// Add an event listener to the document to handle radio button changes
document.addEventListener('DOMContentLoaded', function () {
    var orgStoreTemplateRadio = document.getElementById('id_org_store_template');
    var isOrgStoreCheckbox = document.getElementById('id_is_org_store');
    var branchStoreTemplateRadio = document.getElementById('id_branch_store_template');
    var isBranchStoreCheckbox = document.getElementById('id_is_branch_store');

    var storedOrgStoreTemplateState = localStorage.getItem('orgStoreTemplateState');
    var storedBranchStoreTemplateState = localStorage.getItem('branchStoreTemplateState');

    // Set default values if local storage is empty
    if (!storedOrgStoreTemplateState && !storedBranchStoreTemplateState) {
        orgStoreTemplateRadio.checked = true;
        isOrgStoreCheckbox.checked = true;
        localStorage.setItem('orgStoreTemplateState', 'checked');
    } else {
        orgStoreTemplateRadio.checked = storedOrgStoreTemplateState === 'checked';
        isOrgStoreCheckbox.checked = storedOrgStoreTemplateState === 'checked';

        branchStoreTemplateRadio.checked = storedBranchStoreTemplateState === 'checked';
        isBranchStoreCheckbox.checked = storedBranchStoreTemplateState === 'checked';
    }
});

document.addEventListener('change', function (event) {
    var orgStoreTemplateRadio = document.getElementById('id_org_store_template');
    var isOrgStoreCheckbox = document.getElementById('id_is_org_store');
    var branchStoreTemplateRadio = document.getElementById('id_branch_store_template');
    var isBranchStoreCheckbox = document.getElementById('id_is_branch_store');

    if (event.target.type === 'radio') {
        if (event.target.id === 'id_org_store_template') {
            branchStoreTemplateRadio.checked = false;
            isOrgStoreCheckbox.checked = true;
            isBranchStoreCheckbox.checked = false;

            if (event.target.checked) {
                localStorage.setItem('orgStoreTemplateState', 'checked');
                localStorage.removeItem('branchStoreTemplateState');
            }
        } else if (event.target.id === 'id_branch_store_template') {
            orgStoreTemplateRadio.checked = false;
            isBranchStoreCheckbox.checked = true;
            isOrgStoreCheckbox.checked = false;

            if (event.target.checked) {
                localStorage.setItem('branchStoreTemplateState', 'checked');
                localStorage.removeItem('orgStoreTemplateState');
            }
        }
    } else if (event.target.type === 'checkbox') {
        // Handle checkbox changes if needed
    }
});

//==============================================================
document.addEventListener('DOMContentLoaded', function () {
    var orgStoreTemplateRadio = document.getElementById('id_org_store_template');
    var branchStoreTemplateRadio = document.getElementById('id_branch_store_template');
    var orgTempImage = document.getElementById('org_temp');
    var branchTempImage = document.getElementById('branch_temp');

    // Retrieve the stored state from local storage
    var storedState = localStorage.getItem('selectedStoreTemplate');

    // Set the initial state based on the stored value or default to 'org'
    if (storedState === 'branch') {
        branchStoreTemplateRadio.checked = true;
        orgTempImage.style.display = 'none';
        branchTempImage.style.display = 'block';
    } else {
        orgStoreTemplateRadio.checked = true;
        orgTempImage.style.display = 'block';
        branchTempImage.style.display = 'none';
        localStorage.setItem('selectedStoreTemplate', 'org');
    }

    // Add event listeners to handle radio button changes
    orgStoreTemplateRadio.addEventListener('change', function () {
        localStorage.setItem('selectedStoreTemplate', 'org');
        orgTempImage.style.display = 'block';
        branchTempImage.style.display = 'none';
    });

    branchStoreTemplateRadio.addEventListener('change', function () {
        localStorage.setItem('selectedStoreTemplate', 'branch');
        orgTempImage.style.display = 'none';
        branchTempImage.style.display = 'block';
    });
});