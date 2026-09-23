// ====================================================
// LOGIN
// ====================================================
const loginForm = document.getElementById("login-form");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        // Validación local antes de llamar a la API
        if (!email && !password) {
            mostrarError("⚠️ Debes ingresar tu email y contraseña.");
            return;
        }
        if (!email) {
            mostrarError("⚠️ Debes ingresar tu email.");
            document.getElementById("email").focus();
            return;
        }
        if (!password) {
            mostrarError("⚠️ Debes ingresar tu contraseña.");
            document.getElementById("password").focus();
            return;
        }

        // Validación de formato de email
        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(email)) {
            mostrarError("⚠️ El formato del email no es válido. Ejemplo: usuario@dominio.com");
            document.getElementById("email").focus();
            return;
        }

        // Deshabilitar el botón mientras se hace la petición
        const boton = loginForm.querySelector("button[type='submit']");
        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.textContent = "Iniciando sesión...";

        const { ok, data } = await apiFetch("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
            skipAuthRedirect: true,
        });

        // Restaurar el botón
        boton.disabled = false;
        boton.textContent = textoOriginal;

        if (ok) {
            localStorage.setItem("access_token", data.access_token);
            window.location.href = "/dashboard";
        } else {
            // Mensajes claros según el tipo de error
            let mensaje = "❌ El email o la contraseña son incorrectos. Verifica tus datos e intenta de nuevo.";

            if (data && data.error) {
                // Personalizar el mensaje de "Credenciales inválidas"
                if (data.error.toLowerCase().includes("credenciales")) {
                    mensaje = "❌ El email o la contraseña son incorrectos. Verifica tus datos e intenta de nuevo.";
                } else {
                    mensaje = "❌ " + data.error;
                }
            }

            mostrarError(mensaje);
            // Limpiar solo la contraseña (para que el usuario no tenga que reescribir el email)
            document.getElementById("password").value = "";
            document.getElementById("password").focus();
        }
    });
}

// ====================================================
// REGISTRO
// ====================================================
const registroForm = document.getElementById("registro-form");
if (registroForm) {
    registroForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        // Validaciones locales
        if (!email && !password) {
            mostrarError("⚠️ Debes completar todos los campos.");
            return;
        }
        if (!email) {
            mostrarError("⚠️ Debes ingresar un email.");
            document.getElementById("email").focus();
            return;
        }
        if (!password) {
            mostrarError("⚠️ Debes ingresar una contraseña.");
            document.getElementById("password").focus();
            return;
        }

        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(email)) {
            mostrarError("⚠️ El formato del email no es válido. Ejemplo: usuario@dominio.com");
            document.getElementById("email").focus();
            return;
        }

        if (password.length < 8) {
            mostrarError("⚠️ La contraseña debe tener al menos 8 caracteres.");
            document.getElementById("password").focus();
            return;
        }

        // Deshabilitar botón
        const boton = registroForm.querySelector("button[type='submit']");
        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.textContent = "Creando cuenta...";

        const { ok, data } = await apiFetch("/auth/registro", {
            method: "POST",
            body: JSON.stringify({ email, password }),
            skipAuthRedirect: true,
        });

        boton.disabled = false;
        boton.textContent = textoOriginal;

        if (ok) {
            alert("✅ ¡Cuenta creada con éxito! Ahora inicia sesión.");
            window.location.href = "/login";
        } else {
            let mensaje = "❌ Error al crear la cuenta. Intenta de nuevo.";

            if (data && data.error) {
                if (data.error.toLowerCase().includes("email ya está registrado")) {
                    mensaje = "❌ Ese email ya está registrado. Prueba con otro o inicia sesión.";
                } else if (data.error.toLowerCase().includes("formato del email")) {
                    mensaje = "❌ El formato del email no es válido. Ejemplo: usuario@dominio.com";
                } else if (data.error.toLowerCase().includes("8 caracteres")) {
                    mensaje = "❌ La contraseña debe tener al menos 8 caracteres.";
                } else {
                    mensaje = "❌ " + data.error;
                }
            }

            mostrarError(mensaje);
        }
    });
}

// ====================================================
// LOGOUT
// ====================================================
const btnLogout = document.getElementById("btn-logout");
if (btnLogout) {
    btnLogout.addEventListener("click", () => {
        if (confirm("¿Seguro que quieres cerrar sesión?")) {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
        }
    });
}

// ====================================================
// PROTECCIÓN DE DASHBOARD
// ====================================================
if (window.location.pathname === "/dashboard") {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
    }
}