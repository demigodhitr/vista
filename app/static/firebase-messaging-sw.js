importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");
importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js");

const firebaseConfig = {
    apiKey: "AIzaSyB3kpvlEUvWlSKvknmAAIMy4SJ0fbOXqGM",
    authDomain: "exchange-vista-p-1723312807252.firebaseapp.com",
    projectId: "exchange-vista-p-1723312807252",
    storageBucket: "exchange-vista-p-1723312807252.appspot.com",
    messagingSenderId: "644563502959",
    appId: "1:644563502959:web:894a62086aea2b75cd0a9a",
    measurementId: "G-HJXPJHTW8W"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage(payload => {
    console.log('You Received background message ', payload);
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: payload.notification.icon
    };

        self.registration.showNotification(notificationTitle, notificationOptions);
    });