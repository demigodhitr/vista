document.addEventListener('DOMContentLoaded', function () {
    const offcanvasElement = document.getElementById('action-canvas');

    // Ensure the offcanvas is visible during the animation
    offcanvasElement.addEventListener('show.bs.offcanvas', function () {
        offcanvasElement.classList.add('showing');
        offcanvasElement.classList.remove('hiding');
        offcanvasElement.classList.add('show');
    });

    // Remove animation class after showing animation is done
    offcanvasElement.addEventListener('shown.bs.offcanvas', function () {
        offcanvasElement.classList.remove('showing');
    });

    // Start hiding animation
    offcanvasElement.addEventListener('hide.bs.offcanvas', function () {
        offcanvasElement.classList.add('hiding');
        offcanvasElement.classList.remove('show');
    });

    // Ensure the element is hidden after the hiding animation
    offcanvasElement.addEventListener('hidden.bs.offcanvas', function () {
        offcanvasElement.classList.remove('hiding');
    });
});