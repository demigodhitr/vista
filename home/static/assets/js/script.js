// document.addEventListener("DOMContentLoaded", function () {
//   const testimonials = [
//     {
//       name: "Ava Rock",
//       role: "Financial Planner",
//       image: "assets/img/testimonial/1.jpg",
//       feedback: "“Lorem ipsum dolor sit ametion consectetur adipisicing elit. Ulti amet officiis optio sequi aliquid provident totam.”",
//       rating: 5,
//     },
//     // Add more testimonials as needed
//   ];

//   const testimonialContainer = document.getElementById("testimonial-carousel");

//   testimonials.forEach((testimonial) => {
//     const testimonialElement = document.createElement("div");
//     testimonialElement.classList.add("single-testimoinal-item");

//     testimonialElement.innerHTML = `
//             <div class="client-info">
//                 <div class="client-img bg-cover" style="background-image: url('${testimonial.image}');"></div>
//                 <div class="client-name">
//                     <h6>${testimonial.name}</h6>
//                     <span>${testimonial.role}</span>
//                 </div>
//             </div>
//             <div class="feedback">
//                 ${testimonial.feedback}
//             </div>
//             <div class="rating">
//                 ${Array.from({ length: testimonial.rating }, () => '<i class="fas fa-star"></i>').join("")}
//             </div>
//         `;

//     testimonialContainer.appendChild(testimonialElement);
//   });
// });
