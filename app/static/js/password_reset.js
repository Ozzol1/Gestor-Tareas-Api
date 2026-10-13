// ====================================================
// OLVIDÉ MI CONTRASEÑA - Formulario
// ====================================================
const olvideForm = document.getElementById("olvide-form");
if (olvideForm) {
    olvideForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const email = document.getElementById("email").value.trim();

        if (!email) {
            mostrarError("⚠️ Debes ingresar tu email.");
            return;
        }

        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(email)) {
            mostrarError("⚠️ El formato del email no es válido. Ejemplo: usuario@dominio.com");
            return;
        }

        const boton = olvideForm.querySelector("button[type='submit']");
        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.innerHTML = '<span class="spinner"></span>Enviando...';

        const [respuesta] = await Promise.all([
            apiFetch("/auth/olvide-password", {
                method: "POST",
                body: JSON.stringify({ email }),
                skipAuthRedirect: true,
            }),
            new Promise(resolve => setTimeout(resolve, 500))
        ]);

        const { ok, data } = respuesta;

        boton.disabled = false;
        boton.textContent = textoOriginal;

        if (ok) {
            const modal = document.getElementById("modal-email-enviado");
            if (modal) {
                modal.classList.remove("hidden");

                setTimeout(() => {
                    window.location.href = "/login";
                }, 3000);
            } else {
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
            }
        } else {
            mostrarError(data.error || "Error al enviar el email. Intenta de nuevo.");
        }
    });
}


// ====================================================
// RESET PASSWORD - Formulario
// ====================================================
const resetForm = document.getElementById("reset-form");
if (resetForm) {
    resetForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const password = document.getElementById("password").value;
        const passwordConfirm = document.getElementById("password_confirm").value;

        if (!password || !passwordConfirm) {
            mostrarError("⚠️ Debes completar ambos campos.");
            return;
        }

        if (password.length < 8) {
            mostrarError("⚠️ La contraseña debe tener al menos 8 caracteres.");
            return;
        }

        if (password !== passwordConfirm) {
            mostrarError("⚠️ Las contraseñas no coinciden.");
            return;
        }

        const boton = resetForm.querySelector("button[type='submit']");
        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.innerHTML = '<span class="spinner"></span>Actualizando...';

        const [respuesta] = await Promise.all([
            apiFetch(`/auth/reset-password/${window.RESET_TOKEN}`, {
                method: "POST",
                body: JSON.stringify({ password }),
                skipAuthRedirect: true,
            }),
            new Promise(resolve => setTimeout(resolve, 500))
        ]);

        const { ok, data } = respuesta;

        boton.disabled = false;
        boton.textContent = textoOriginal;

        if (ok) {
            const modal = document.getElementById("modal-password-cambiada");
            if (modal) {
                modal.classList.remove("hidden");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 2800);
            } else {
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
            }
        } else {
            mostrarError(data.error || "Error al actualizar la contraseña.");
        }
    });
}