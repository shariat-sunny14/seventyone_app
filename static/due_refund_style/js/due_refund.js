// nav and tabs always selected after refresh start
$(document).ready(function () {
    $('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        var activeTab = $(e.target).attr('href');
        localStorage.setItem('activeTab', activeTab);
    });

    var activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        $('#myTab a[href="' + activeTab + '"]').tab('show');
    }
});
// nav and tabs always selected after refresh end
