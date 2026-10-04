document.addEventListener(
    "DOMContentLoaded",
    () => {

        const btn =
            document.querySelector(
                ".save-btn"
            );

        btn.addEventListener(
            "mouseenter",
            () => {
                btn.style.boxShadow =
                    "0 10px 30px rgba(105,129,141,.4)";
            }
        );

        btn.addEventListener(
            "mouseleave",
            () => {
                btn.style.boxShadow =
                    "none";
            }
        );

    }
);