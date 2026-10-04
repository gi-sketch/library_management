document.addEventListener(
    "DOMContentLoaded",
    () => {

        const card =
            document.querySelector(
                ".register-card"
            );

        card.addEventListener(
            "mouseenter",
            () => {
                card.style.transform =
                    "translateY(-5px)";
            }
        );

        card.addEventListener(
            "mouseleave",
            () => {
                card.style.transform =
                    "translateY(0)";
            }
        );

    }
);