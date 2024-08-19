/* ===================================================================
    Author          : DiscreteDev
    Version         : 1.0
* ================================================================= */

(function ($) {
  "use strict";

  $(document).ready(function () {



    new WOW().init();



    /* =============================================
        # Sliders init
    ===============================================*/
    var swiper = new Swiper(".testimonial-carousel-active", {
      slidesPerView: 1,
      spaceBetween: 10,
      centeredSlides: true,
      loop: true,
      autoplay: {
        delay: 2500,
        disableOnInteraction: false,
      },
      pagination: {
        el: ".testimonial__pagination",
        clickable: true,
      },
      breakpoints: {
        768: {
          slidesPerView: 2,
          spaceBetween: 20,
        },
        1200: {
          slidesPerView: 3,
          spaceBetween: 50,
        },
      },
    });



    // team Section

    var swiper = new Swiper(".team-slider", {
      slidesPerView: 1,
      spaceBetween: 10,
      loop: true,
      autoplay: {
        delay: 2500,
        disableOnInteraction: false,
      },
      pagination: {
        el: ".team__pagination",
        clickable: true,
      },
      breakpoints: {
        575: {
          slidesPerView: 2,
          spaceBetween: 20,
        },
        992: {
          slidesPerView: 3,
          spaceBetween: 50,
        },
        1200: {
          slidesPerView: 4,
          spaceBetween: 50,
        },
      },
    });


    /* =============================================
        # Magnific popup init
    ===============================================*/
    $(".popup-link").magnificPopup({
      type: 'image',
      fixedContentPos: false
    });

    $(".popup-gallery").magnificPopup({
      type: 'image',
      fixedContentPos: false,
      gallery: {
        enabled: true
      },
      // other options
    });

    $(".popup-video, .popup-vimeo, .popup-gmaps").magnificPopup({
      type: "iframe",
      mainClass: "mfp-fade",
      removalDelay: 160,
      preloader: false,
      fixedContentPos: false
    });

    //# Smooth Scroll
    $('#responsive-menu a').on('click', function (event) {
      var $anchor = $(this);
      var headerH = '85';
      $('html, body').stop().animate({
        scrollTop: $($anchor.attr('href')).offset().top - headerH + "px"
      }, 1000, 'easeInOutExpo');
      event.preventDefault();
    });

    // Sticky Menu
    $(window).scroll(function () {
      var Width = $(document).width();

      if ($("body").scrollTop() > 100 || $("html").scrollTop() > 100) {
        if (Width > 767) {
          $("header").addClass("sticky");
        }
      } else {
        $("header").removeClass("sticky");
      }
    });

    $('.container').imagesLoaded(function () {
      $('.portfolio-cat-filter').on('click', 'button', function () {
        var filterValue = $(this).attr('data-filter');
        $grid.isotope({
          filter: filterValue
        });
      });

      var $grid = $('.grid').isotope({
        itemSelector: '.grid-item',
        percentPosition: true,
      });
    });

    var catButton = '.portfolio-cat-filter button';

    $(catButton).on('click', function () {
      $(catButton).removeClass('active');
      $(this).addClass('active');
    });

    $('#hamburger').on('click', function () {
      $('.mobile-nav').addClass('show');
      $('.overlay').addClass('active');
    });

    $('.close-nav').on('click', function () {
      $('.mobile-nav').removeClass('show');
      $('.overlay').removeClass('active');
    });

    $(".overlay").on("click", function () {
      $(".mobile-nav").removeClass("show");
      $('.overlay').removeClass('active');
    });

    $("#mobile-menu").metisMenu();

    /*---------------------------------------------
    Scroll up
    ---------------------------------------------*/
    $.scrollUp({
      scrollName: 'scrollUp', // Element ID
      topDistance: '1110', // Distance from top before showing element (px)
      topSpeed: 2000, // Speed back to top (ms)
      animation: 'slide', // Fade, slide, none
      animationInSpeed: 300, // Animation in speed (ms)
      animationOutSpeed: 300, // Animation out speed (ms)
      scrollText: '<i class="fal fa-angle-up"></i>', // Text for element
      activeOverlay: false, // Set CSS color to display scrollUp active point, e.g '#00FFFF'
    });

  }); // end document ready function


  function loader() {
    $(window).on('load', function () {
      // Animate loader off screen
      $(".preloader").addClass('loaded');
      $(".preloader").delay(700).fadeOut();
    });
  }


  /*--------------------------------------------------------------
Ajax Contact Form And Appointment
--------------------------------------------------------------*/
  //contact form js
  $(function () {
    // Get the form.
    var form = $('#contact-form');
    // Get the messages div.
    var formMessages = $('.form-message');
    // Set up an event listener for the contact form.
    $(form).submit(function (e) {
      // Stop the browser from submitting the form.
      e.preventDefault();
      // Serialize the form data.
      var formData = $(form).serialize();
      // Submit the form using AJAX.
      $.ajax({
        type: 'POST',
        url: $(form).attr('action'),
        data: formData
      })
        .done(function (response) {
          // Make sure that the formMessages div has the 'success' class.
          $(formMessages).removeClass('error');
          $(formMessages).addClass('success');
          // Set the message text.
          $(formMessages).text(response);
          // Clear the form.
          $('#contact-form input, #contact-form textarea').val('');
        })
        .fail(function (data) {
          // Make sure that the formMessages div has the 'problem' class.
          $(formMessages).removeClass('success');
          $(formMessages).addClass('problem');
          // Set the message text.
          if (data.responseText !== '') {
            $(formMessages).text(data.responseText);
          } else {
            $(formMessages).text('Oops! An error occured and your message could not be sent.');
          }
        });
    });
  });

  loader();
})(jQuery); // End jQuery