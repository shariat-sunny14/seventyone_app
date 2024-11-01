/*==================== SHOW NAVBAR ====================*/
const showMenu = (headerToggle, navbarId) => {
    const toggleBtn = document.getElementById(headerToggle),
        nav__menu = document.getElementById(navbarId);

    // Validate that variables exist
    if (toggleBtn && nav__menu) {
        toggleBtn.addEventListener('click', () => {
            // We add the show-menu class to the div tag with the nav__menu class
            nav__menu.classList.toggle('show-menu');
            // Change icon and rotate it
            toggleBtn.classList.toggle('bx-x');
            toggleBtn.querySelector('.nav__dropdown-icon').style.transform =
                nav__menu.classList.contains('show-menu') ? 'rotate(180deg)' : 'rotate(0deg)';
        });
    }
};

// dropdown click wise show
document.addEventListener("DOMContentLoaded", function () {
    // Your showMenu function
    showMenu('header-toggle', 'navbar');

    var dropdowns = document.querySelectorAll(".nav__dropdown");

    dropdowns.forEach(function (dropdown) {
        dropdown.addEventListener("click", function (event) {
            // Toggle the class "active" to show/hide the dropdown content
            this.classList.toggle("active");

            // Rotate the dropdown-icon
            this.querySelector('.nav__dropdown-icon').style.transform =
                this.classList.contains("active") ? 'rotate(180deg)' : 'rotate(0deg)';

            // Store the state in localStorage
            var state = this.classList.contains("active") ? "active" : "inactive";
            localStorage.setItem(this.id + "-state", state);

            // Prevent closing other dropdowns when one is clicked
            event.stopPropagation();
        });
    });
});

/*==================== LINK ACTIVE ====================*/

document.addEventListener("DOMContentLoaded", function () {
    const menuLinks = document.querySelectorAll(".nav__link");
    const menuLinkMenus = document.querySelectorAll(".nav__link__menu");

    window.setActiveLink = function () {
        const currentPath = window.location.pathname;
        menuLinks.forEach(link => {
            const parentDropdown = link.closest('.nav__dropdown');
            if (parentDropdown) {
                const parentMenu = parentDropdown.querySelector('.nav__link__menu');
                if (link.getAttribute("href") === currentPath) {
                    link.classList.add("active");
                    if (parentMenu) {
                        parentMenu.classList.add("active");
                    }
                } else {
                    link.classList.remove("active");
                }
            }
        });

        // Update nav__link__menu active state
        menuLinkMenus.forEach(menu => {
            const hasActiveLink = menu.nextElementSibling.querySelector('.nav__link.active') !== null;
            if (!hasActiveLink) {
                menu.classList.remove("active");
            }
        });
    }

    // Initial call to set the active link based on the current URL
    setActiveLink();

    // Event listener for clicks on menu links
    menuLinks.forEach(link => {
        link.addEventListener("click", function () {
            // Remove active class from all links
            menuLinks.forEach(link => link.classList.remove("active"));
            menuLinkMenus.forEach(menu => menu.classList.remove("active"));

            // Add active class to the clicked link
            link.classList.add("active");
            const parentDropdown = link.closest('.nav__dropdown');
            if (parentDropdown) {
                const parentMenu = parentDropdown.querySelector('.nav__link__menu');
                if (parentMenu) {
                    parentMenu.classList.add("active");
                }
            }

            // Store the active link's href in localStorage
            localStorage.setItem("activeLink", link.getAttribute("href"));
        });
    });

    // Check and set the active link based on localStorage on page load
    const activeLink = localStorage.getItem("aactiveLink");
    if (activeLink && activeLink !== window.location.pathname) {
        // Update the URL without reloading the page
        window.history.pushState(null, null, activeLink);
    }

    // Set the active link based on the current URL or localStorage
    setActiveLink();

    // Listen for URL changes and set the active link accordingly
    window.addEventListener("popstate", setActiveLink);

    // Listen for manual URL changes (such as typing in the URL bar)
    window.addEventListener("load", setActiveLink);
});

function navigateTo(url) {
    localStorage.setItem("activeLink", url);
    window.history.pushState(null, null, url);
    setActiveLink(); // Update active link before changing location
    location.href = url; // Trigger page load after setting active link
}

/*==================== LINK ACTIVE END ====================*/


// Date picker
$(document).ready(function () {
    $(".datepicker").datepicker({
        dateFormat: 'yy-mm-dd',
        changeYear: true,
        changeMonth: true
    });
});


// circle loader
function circleloaderstart() {
    document.getElementById('circleloader').style.display = 'grid';
}

function circleloaderstop() {
    setTimeout(function () {
        document.getElementById('circleloader').style.display = 'none';
    }, 1100);
}

// line loader
function lineloaderstart() {
    document.getElementById('line_loader').style.display = 'flex';
}

function lineloaderstop() {
    setTimeout(function () {
        document.getElementById('line_loader').style.display = 'none';
    }, 1100);
}

// tab panel click open loader
$(document).ready(function () {
    // When a nav-link is clicked
    $('.nav-link').on('click', function () {
        // Check if it is the active link
        if ($(this).hasClass('active')) {
            lineloaderstart();
            setTimeout(lineloaderstop, 1100); // Hide after 5 seconds
        }
    });
});

//tab content show hide #example: type,uom,category,supplier,manufecturer etc setup tab  
document.addEventListener("DOMContentLoaded", function () {
    // Attach a click event listener to each tab link
    var tabLinks = document.querySelectorAll('.nav-link');

    tabLinks.forEach(function (tabLink) {
        tabLink.addEventListener('click', function (event) {
            // Prevent the default behavior of the anchor tag
            event.preventDefault();

            // Get the target tab and its content
            var tabId = this.getAttribute('href').substring(1);
            var tabContent = document.getElementById(tabId);

            // Hide all tabs and their contents
            hideAllTabs();

            // Show the clicked tab and its content
            this.classList.add('active');
            tabContent.classList.add('show', 'active');

            // Store the active tab in localStorage
            localStorage.setItem('activeTab', tabId);
        });
    });

    // Load the active tab from localStorage on page load
    var activeTabId = localStorage.getItem('activeTab');
    if (activeTabId) {
        var activeTabLink = document.querySelector(`.nav-link[href="#${activeTabId}"]`);
        if (activeTabLink) {
            activeTabLink.click();
        }
    }
});

function hideAllTabs() {
    // Hide all tabs and their contents
    var allTabs = document.querySelectorAll('.nav-link');
    var allContents = document.querySelectorAll('.tab-pane');

    allTabs.forEach(function (tab) {
        tab.classList.remove('active');
    });

    allContents.forEach(function (content) {
        content.classList.remove('show', 'active');
    });
}
