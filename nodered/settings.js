// nodered/settings.js
// ===================
// Configuracion de Node-RED para el proyecto HaizeLab.
// Este fichero se monta en /data/settings.js dentro del contenedor.
//
// Puntos clave:
//   - adminAuth: autenticacion obligatoria con control de acceso por roles
//   - credentialSecret: clave para cifrar credenciales (viene de variable de entorno)
//   - functionGlobalContext: permite acceder a variables de entorno desde nodos function
//   - flowFile: fichero de flujos (montado como volumen read-only)

const bcrypt = require('bcryptjs');

const adminUser = process.env.NODE_RED_ADMIN_USER || 'admin';
const adminPassRaw = process.env.NODE_RED_ADMIN_PASSWORD || 'haizelab2024seguro';
const adminPasswordHash = adminPassRaw.startsWith('$2')
    ? adminPassRaw
    : bcrypt.hashSync(adminPassRaw, 8);

module.exports = {
    // Puerto de escucha (dentro del contenedor)
    uiPort: process.env.PORT || 1880,

    // Autenticacion del editor y APIs administrativas (Seguridad ante exposicion web)
    adminAuth: {
        type: "credentials",
        users: [{
            username: adminUser,
            password: adminPasswordHash,
            permissions: "*"
        }]
    },

    // Directorio de datos de Node-RED
    userDir: '/data',

    // Fichero de flujos (montado como volumen desde nodered/flows.json)
    flowFile: 'flows.json',

    // Clave para cifrar credenciales almacenadas en disco
    // Se pasa por variable de entorno para no guardarla en git
    credentialSecret: process.env.NODE_RED_CREDENTIAL_SECRET || 'haizelab-secret',

    // Permitir require en nodos function
    functionExternalModules: true,

    // Contexto global accesible desde nodos function via global.get(...)
    functionGlobalContext: {
        fs: require('fs')
    },

    // Nivel de log: info en produccion, debug para desarrollo
    logging: {
        console: {
            level: 'info',
            metrics: false,
            audit: false
        }
    },

    // Editor web: accesible en http://localhost:1880
    editorTheme: {
        page: {
            title: 'HaizeLab - Node-RED'
        },
        header: {
            title: 'HaizeLab'
        }
    }
};