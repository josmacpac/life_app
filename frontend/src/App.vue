<script setup>
import { ref, watch, onMounted } from 'vue'

const API_BASE = '/api'

const currentView = ref('home')
const sessionName = ref('')
const userName = ref('')
const isHost = ref(false)
const joinCode = ref('')
const joinName = ref('')
const showCodeModal = ref(false)
const createdCode = ref('')
const createdName = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const boardSessionName = ref('')
const boardSessionCode = ref('')
const boardIsHost = ref(false)
const boardToken = ref('')
const confirmClose = ref(false)
const recoverToken = ref('')
const players = ref([])

// Estado del tablero (vista jugador)
const showRuletaModal = ref(false)
const showPerfilModal = ref(false)
const verTableroGeneral = ref(false)
const acordeonAbierto = ref({ profesion: false, inversiones: false, casas: false, familia: false })
const turnoEstado = ref('espera') // 'espera' | 'turno' | 'jubilado'
const dineroAcumulado = ref(0)
const tarjetasObtenidas = ref([])

const girarRuleta = () => {
  if (turnoEstado.value !== 'turno') return
  showRuletaModal.value = true
}

const toggleAcordeon = (seccion) => {
  acordeonAbierto.value = { ...acordeonAbierto.value, [seccion]: !acordeonAbierto.value[seccion] }
}

const STATE_KEY = 'life_app_state'

const guardarEstado = () => {
  const estado = {
    currentView: currentView.value,
    boardSessionName: boardSessionName.value,
    boardSessionCode: boardSessionCode.value,
    boardIsHost: boardIsHost.value,
    boardToken: boardToken.value,
  }
  try {
    localStorage.setItem(STATE_KEY, JSON.stringify(estado))
  } catch (e) {
    console.error('No se pudo guardar el estado:', e)
  }
}

const limpiarEstadoTablero = () => {
  currentView.value = 'home'
  boardSessionName.value = ''
  boardSessionCode.value = ''
  boardIsHost.value = false
  boardToken.value = ''
  players.value = []
  try {
    localStorage.removeItem(STATE_KEY)
  } catch (e) {
    console.error('No se pudo limpiar el estado:', e)
  }
}

const restaurarEstado = () => {
  try {
    const raw = localStorage.getItem(STATE_KEY)
    if (!raw) return
    const estado = JSON.parse(raw)
    if (estado.currentView) currentView.value = estado.currentView
    if (estado.boardSessionName) boardSessionName.value = estado.boardSessionName
    if (estado.boardSessionCode) boardSessionCode.value = estado.boardSessionCode
    if (estado.boardIsHost !== undefined) boardIsHost.value = estado.boardIsHost
    if (estado.boardToken) boardToken.value = estado.boardToken
  } catch (e) {
    console.error('No se pudo restaurar el estado:', e)
  }
}

onMounted(() => {
  restaurarEstado()
  if (currentView.value === 'board' && boardSessionCode.value) {
    fetchPlayers()
  }
})

watch([currentView, boardSessionName, boardSessionCode, boardIsHost, boardToken], () => {
  guardarEstado()
}, { deep: true })


const fetchPlayers = async () => {
  if (!boardSessionCode.value) return
  try {
    const res = await fetch(`${API_BASE}/sessions/${boardSessionCode.value}/players`)
    if (res.ok) {
      const data = await res.json()
      players.value = data.players || []
    }
  } catch (err) {
    console.error('Error al obtener jugadores:', err)
  }
}

const setMode = (mode) => {
  currentView.value = mode
  error.value = ''
  success.value = ''
}

watch(isHost, (newVal) => {
  if (!newVal) {
    userName.value = ''
  }
})

const guardarToken = (token) => {
  if (token) {
    localStorage.setItem('life_app_token', token)
    boardToken.value = token
  }
}

const obtenerTokenGuardado = () => {
  const saved = localStorage.getItem('life_app_token')
  if (saved) {
    recoverToken.value = saved
    return saved
  }
  return null
}

const crearSesion = async () => {
  const nombreUsuario = isHost.value ? 'Anfitrión' : userName.value.trim()
  if (!isHost.value && !nombreUsuario) {
    error.value = 'Ingresa tu nombre de usuario'
    return
  }
  if (!sessionName.value.trim()) {
    error.value = 'Ingresa un nombre para la sesión'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: sessionName.value.trim(),
        host: isHost.value,
      }),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'No se pudo crear la sesión')
    }

    const data = await res.json()
    createdCode.value = data.session_code
    createdName.value = nombreUsuario
    boardSessionName.value = sessionName.value.trim()
    boardSessionCode.value = data.session_code
    boardIsHost.value = isHost.value
    boardToken.value = data.player_token || data.host_token || ''
    guardarToken(boardToken.value)
    showCodeModal.value = true
    success.value = 'Sesión creada correctamente'
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const unirseSesion = async () => {
  if (!joinCode.value.trim() || !joinName.value.trim()) {
    error.value = 'Ingresa el código y tu nombre'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const res = await fetch(`${API_BASE}/sessions/${joinCode.value.trim()}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: joinName.value.trim() }),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'No se pudo unir a la sesión')
    }

    const data = await res.json()
    boardSessionName.value = joinCode.value.trim()
    boardSessionCode.value = data.session_code
    boardIsHost.value = false
    boardToken.value = data.player_token || ''
    guardarToken(boardToken.value)
    currentView.value = 'board'
    fetchPlayers()
    success.value = 'Te uniste a la sesión'
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const recuperarSesion = async () => {
  const token = obtenerTokenGuardado()
  if (!token) {
    error.value = 'No se encontró un token guardado. Regístrate con un nombre de usuario.'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const res = await fetch(`${API_BASE}/sessions/reconnect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'No se pudo recuperar la sesión')
    }

    const data = await res.json()
    if (data.type === 'host') {
      boardSessionName.value = data.session_code
      boardSessionCode.value = data.session_code
      boardIsHost.value = true
      boardToken.value = token
    } else if (data.type === 'player') {
      boardSessionName.value = data.session_code
      boardSessionCode.value = data.session_code
      boardIsHost.value = data.is_creator
      boardToken.value = token
    }
    currentView.value = 'board'
    fetchPlayers()
    success.value = 'Sesión recuperada'
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const irAlTablero = () => {
  showCodeModal.value = false
  currentView.value = 'board'
  fetchPlayers()
}

const copiarCodigo = () => {
  navigator.clipboard.writeText(createdCode.value)
  success.value = 'Código copiado al portapapeles'
  setTimeout(() => { success.value = '' }, 2000)
}

const cerrarModal = () => {
  showCodeModal.value = false
  createdCode.value = ''
  sessionName.value = ''
  userName.value = ''
  limpiarEstadoTablero()
}

const abrirConfirmarCerrar = () => {
  confirmClose.value = true
}

const cerrarSesion = async () => {
  if (!boardSessionCode.value || !boardToken.value) {
    error.value = 'No hay sesión activa para cerrar'
    return
  }

  loading.value = true
  error.value = ''
  confirmClose.value = false

  try {
    const res = await fetch(`${API_BASE}/sessions/${boardSessionCode.value}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: boardToken.value }),
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'No se pudo cerrar la sesión')
    }

    const data = await res.json()
    limpiarEstadoTablero()
    success.value = 'Sesión cerrada correctamente'
    localStorage.removeItem('life_app_token')
  } catch (err) {
    error.value = err.message
    confirmClose.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-b from-secondary via-white to-secondary">

    <!-- VISTA HOME: acordeón crear / unirse -->
    <div v-if="currentView === 'home' || currentView === 'create' || currentView === 'join'" class="w-full max-w-md">
      <header class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-primary tracking-tight">Life App</h1>
        <p class="text-secondary-dark mt-2 text-sm">Crea o únete a una partida</p>
      </header>

      <div class="bg-white rounded-3xl shadow-2xl p-6 border border-secondary/30 overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-2 bg-primary"></div>

        <h2 class="text-xl font-bold text-gray-800 mb-6 text-center">¿Qué deseas hacer?</h2>

        <!-- Acordeón -->
        <div class="space-y-3">

          <!-- Botón Crear sesión -->
          <div class="group">
            <button
              @click="setMode('create')"
              class="w-full py-5 px-6 rounded-2xl font-bold text-left text-gray-800 bg-secondary/20 border border-secondary/40 hover:bg-secondary/40 hover:border-primary/50 transition-all flex items-center justify-between"
            >
              <span class="flex items-center gap-3">
                <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Crear nueva sesión
              </span>
              <svg class="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div v-if="currentView === 'create'" class="mt-4 bg-white border-t border-gray-100 pt-6">
              <!-- Nota descriptiva -->
              <div class="bg-primary/5 rounded-xl p-3 border border-primary/20 mb-4">
                <div class="flex items-center gap-2 mb-1">
                  <div class="w-2 h-2 rounded-full bg-primary"></div>
                  <span class="text-xs font-bold text-primary uppercase tracking-wider">Crear sesión</span>
                </div>
                <p class="text-xs text-gray-700 leading-relaxed">
                  Eres el anfitrión de la partida. Generas el código que los jugadores usarán para unirse.
                  Desde otro dispositivo, los jugadores se unen con ese código y su nombre.
                </p>
              </div>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Nombre de la sesión</label>
                  <input
                    v-model="sessionName"
                    type="text"
                    placeholder="Ej: Mi partida"
                    class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Tu nombre de usuario</label>
                  <input
                    v-model="userName"
                    type="text"
                    :placeholder="isHost ? 'Anfitrión (automático)' : 'Ej: Jugador 1'"
                    :disabled="isHost"
                    class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                    :class="{ 'border-accent-pink': error.value && !isHost, 'bg-gray-100 text-gray-400 cursor-not-allowed': isHost }"
                  />
                  <p v-if="isHost" class="text-xs text-primary mt-1 text-center">
                    Nombre asignado automáticamente: <strong>Anfitrión</strong>
                  </p>
                </div>

                <div class="bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <p class="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wider">Dispositivo</p>
                  <div class="flex items-center gap-4">
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="deviceMode" value="false" v-model="isHost" class="accent-primary" />
                      <span class="text-sm text-gray-700">Jugador (móvil)</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="deviceMode" value="true" v-model="isHost" class="accent-primary" />
                      <span class="text-sm text-gray-700">Host (tablero completo)</span>
                    </label>
                  </div>
                </div>

                <div v-if="isHost" class="bg-secondary/5 rounded-xl p-3 border border-secondary/20 mt-3">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-2 h-2 rounded-full bg-secondary"></div>
                    <span class="text-xs font-bold text-secondary uppercase tracking-wider">Instrucción para host</span>
                  </div>
                  <p class="text-xs text-secondary-dark leading-relaxed text-center">
                    Inicia sesión desde <strong>otro dispositivo</strong> como jugador usando el código de sesión que se mostrará al crear.
                  </p>
                </div>

                <button
                  @click="crearSesion"
                  :disabled="loading"
                  class="w-full py-4 px-6 rounded-xl font-bold text-white bg-primary hover:bg-secondary transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-lg active:scale-95"
                >
                  {{ loading ? 'Creando...' : 'Crear sesión' }}
                </button>

                <p v-if="error" class="text-sm text-accent-pink bg-accent-pink/10 px-3 py-2 rounded-lg border border-accent-pink/20">
                  {{ error }}
                </p>
                <p v-else-if="success" class="text-sm text-primary bg-primary/10 px-3 py-2 rounded-lg border border-primary/20">
                  {{ success }}
                </p>
              </div>
            </div>
          </div>

          <!-- Botón Unirse a sesión -->
          <div class="group">
            <button
              @click="setMode('join')"
              class="w-full py-5 px-6 rounded-2xl font-bold text-left text-gray-800 bg-secondary/20 border border-secondary/40 hover:bg-secondary/40 hover:border-primary/50 transition-all flex items-center justify-between"
            >
              <span class="flex items-center gap-3">
                <svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.586l1.293-1.293a1 1 0 011.414-1.414z" />
                </svg>
                Unirse a una sesión
              </span>
              <svg class="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div v-if="currentView === 'join'" class="mt-4 bg-white border-t border-gray-100 pt-6">
              <!-- Nota descriptiva -->
              <div class="bg-primary/5 rounded-xl p-3 border border-primary/20 mb-4">
                <div class="flex items-center gap-2 mb-1">
                  <div class="w-2 h-2 rounded-full bg-primary"></div>
                  <span class="text-xs font-bold text-primary uppercase tracking-wider">Unirse a sesión</span>
                </div>
                <p class="text-xs text-gray-700 leading-relaxed">
                  Ingresa el código de sesión que te dio el anfitrión y tu nombre de jugador para entrar a la partida.
                </p>
              </div>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Código de sesión</label>
                  <input
                    v-model="joinCode"
                    type="text"
                    placeholder="Ej: ABCD1234"
                    class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all uppercase"
                    :class="{ 'border-accent-pink': error.value }"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Tu nombre de usuario</label>
                  <input
                    v-model="joinName"
                    type="text"
                    placeholder="Ej: Jugador 1"
                    class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                    :class="{ 'border-accent-pink': error.value }"
                  />
                </div>

                <!-- Opción recuperar sesión -->
                <div class="bg-primary/5 rounded-xl p-3 border border-primary/20">
                  <div class="flex items-center gap-2 mb-3">
                    <div class="w-2 h-2 rounded-full bg-primary"></div>
                    <span class="text-xs font-bold text-primary uppercase tracking-wider">¿Ya jugaste antes?</span>
                  </div>
                  <button
                    @click="recuperarSesion"
                    :disabled="loading"
                    class="w-full py-3 px-4 rounded-lg font-medium text-primary bg-white border border-primary hover:bg-primary/10 transition-all text-sm flex items-center justify-center gap-2"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Recuperar sesión
                  </button>
                  <p v-if="recoverToken" class="text-xs text-gray-500 mt-2 text-center">
                    Token guardado encontrado · Usarlo para reconectar
                  </p>
                  <p v-else class="text-xs text-gray-500 mt-2 text-center">
                    No hay token guardado · Regístrate con un nombre
                  </p>
                </div>

                <button
                  @click="unirseSesion"
                  :disabled="loading"
                  class="w-full py-4 px-6 rounded-xl font-bold text-white bg-primary hover:bg-secondary transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-lg active:scale-95"
                >
                  {{ loading ? 'Uniendo...' : 'Entrar a la sesión' }}
                </button>

                <p v-if="error" class="text-sm text-accent-pink bg-accent-pink/10 px-3 py-2 rounded-lg border border-accent-pink/20">
                  {{ error }}
                </p>
                <p v-else-if="success" class="text-sm text-primary bg-primary/10 px-3 py-2 rounded-lg border border-primary/20">
                  {{ success }}
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>

      <footer class="mt-8 text-center text-sm text-gray-600">
        Partida compartida · Tablero generado una vez por sesión
      </footer>
    </div>

    <!-- VISTA TABLERO -->
    <div v-if="currentView === 'board'" :class="boardIsHost ? 'max-w-4xl' : 'max-w-md w-full p-2'">
      <header class="bg-white rounded-3xl shadow-xl p-4 md:p-6 mb-4 md:mb-6 border border-secondary/30 flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4">
        <!-- Participantes (reservado para Redis) -->
        <div class="bg-gray-50 rounded-xl border border-gray-200 p-3 md:p-4 w-full md:w-64 flex flex-col gap-2">
          <div class="flex items-center gap-2 mb-1 md:mb-2">
            <div class="w-2 h-2 rounded-full bg-primary"></div>
            <span class="text-xs md:text-sm font-bold text-gray-500 uppercase tracking-wider">Participantes</span>
          </div>
          <div class="space-y-1 md:space-y-2" id="participants-list">
            <div v-if="players.length === 0" class="flex items-center gap-2 px-2 md:px-3 py-1 md:py-2 bg-white rounded-lg border border-gray-100 text-xs md:text-sm">
              <div class="w-6 h-6 rounded-full bg-secondary flex items-center justify-center text-primary font-bold text-xs md:text-sm">
                ?
              </div>
              <span class="text-gray-700">Esperando jugadores...</span>
            </div>
            <div v-for="player in players" :key="player.name" class="flex items-center gap-2 px-2 md:px-3 py-1 md:py-2 bg-white rounded-lg border border-gray-100 text-xs md:text-sm">
              <div :class="['w-6 h-6 rounded-full flex items-center justify-center text-primary font-bold text-xs md:text-sm', player.is_creator ? 'bg-accent-pink' : 'bg-secondary']">
                {{ player.name.charAt(0).toUpperCase() }}
              </div>
              <span class="text-gray-700">{{ player.name }}</span>
              <span v-if="player.is_creator" class="ml-auto text-[10px] uppercase tracking-wider text-accent-pink font-bold">Creador</span>
            </div>
          </div>
        </div>

        <div class="flex-1 flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4">
          <div>
            <h2 class="text-lg md:text-xl font-bold text-gray-800 flex items-center gap-2">
              <svg class="w-5 md:w-6 h-5 md:h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              {{ boardSessionName || 'Tablero' }}
            </h2>
            <p class="text-xs md:text-sm text-gray-500 mt-1">Código para unirse: <span class="font-mono font-bold text-primary">{{ boardSessionCode }}</span></p>
          </div>

          <div class="flex flex-wrap gap-1 md:gap-2 justify-center md:justify-end">
            <button
              @click="limpiarEstadoTablero"
              class="px-3 md:px-4 py-2 md:py-2.5 rounded-xl font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 transition-all text-xs md:text-sm"
            >
              Volver
            </button>
            <button
              @click="showPerfilModal = true"
              class="px-3 md:px-4 py-2 md:py-2.5 rounded-xl font-medium text-primary bg-white border border-primary hover:bg-primary/5 transition-all shadow-md text-xs md:text-sm"
            >
              Perfil
            </button>
            <button
              @click="verTableroGeneral = true"
              class="px-3 md:px-4 py-2 md:py-2.5 rounded-xl font-bold text-white bg-secondary hover:bg-secondary/90 transition-all shadow-md text-xs md:text-sm"
            >
              Tablero
            </button>
            <!-- Botón cerrar sesión solo para host -->
            <button
              v-if="boardIsHost"
              @click="abrirConfirmarCerrar"
              class="px-3 md:px-4 py-2 md:py-2.5 rounded-xl font-bold text-accent-pink bg-accent-pink/10 border border-accent-pink/30 hover:bg-accent-pink/20 transition-all text-xs md:text-sm"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <!-- Área del tablero (vista jugador mobile-first) -->
      <div v-if="!boardIsHost" class="bg-secondary/20 rounded-2xl p-4 border border-secondary/40 min-h-[600px] flex flex-col items-center justify-center gap-4">

        <!-- Estado + turno + monto -->
        <div class="w-full flex flex-col md:flex-row gap-4 items-start md:items-center">
          <!-- Caja izquierda: estado -->
          <div class="flex-1 bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-gray-600 uppercase tracking-wider">Estado</span>
              <span
                :class="[
                  'text-xs font-bold px-2 py-0.5 rounded',
                  turnoEstado === 'espera' ? 'bg-accent-yellow/20 text-amber-800 border border-accent-yellow/40' : '',
                  turnoEstado === 'turno' ? 'bg-secondary/20 text-secondary-dark border border-secondary/40' : '',
                  turnoEstado === 'jubilado' ? 'bg-accent-pink/20 text-accent-pink-dark border border-accent-pink/40' : '',
                ]"
              >
                {{ turnoEstado === 'espera' ? 'ESPERA' : turnoEstado === 'turno' ? 'TU TURNO' : 'JUBILADO' }}
              </span>
            </div>
            <button
              @click="girarRuleta"
              :disabled="turnoEstado !== 'turno'"
              class="w-full py-3 rounded-lg font-bold text-white bg-primary hover:bg-secondary transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md active:scale-95"
            >
              Girar ruleta
            </button>
          </div>

          <!-- Caja derecha: monto acumulado -->
          <div class="flex-1 bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-bold text-gray-600 uppercase tracking-wider">Monto acumulado</span>
            </div>
            <div class="text-2xl font-bold text-primary">$ {{ dineroAcumulado.toLocaleString() }}</div>
            <div class="mt-1 flex justify-between text-xs text-gray-500">
              <span>Inversiones: $ {{ dineroAcumulado.toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <!-- Rectángulo vertical: tarjetas obtenidas -->
        <div class="w-full max-w-md flex-1 flex-col items-center gap-2">
          <div class="w-full bg-white rounded-xl p-2 border border-gray-200 shadow-sm flex-1 overflow-hidden">
            <div class="flex items-center gap-2 mb-1">
              <div class="w-1 h-3 bg-primary rounded"></div>
              <span class="text-xs font-bold text-gray-600 uppercase tracking-wider">Tarjetas</span>
            </div>
            <div class="h-full overflow-y-auto flex flex-col gap-1 p-1">
              <div v-for="(tarjeta, idx) in tarjetasObtenidas" :key="idx" class="flex items-center gap-2 px-2 py-1 rounded bg-amber-50 border border-amber-100 text-xs">
                <span class="w-5 h-5 rounded flex items-center justify-center bg-amber-100 text-amber-700 font-bold">{{ tarjeta.inicial || '?' }}</span>
                <span class="text-gray-700">{{ tarjeta.nombre }}</span>
              </div>
              <div v-if="tarjetasObtenidas.length === 0" class="flex items-center justify-center h-8 text-xs text-gray-400">
                Sin tarjetas aún
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Área del tablero (vista host) -->
      <div v-else class="bg-white rounded-3xl shadow-xl p-6 md:p-12 border border-secondary/30 min-h-[500px] flex flex-col items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-full bg-accent-yellow flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span class="text-4xl">🎲</span>
          </div>
          <h3 class="text-2xl font-bold text-gray-800 mb-2">Tablero de juego</h3>
          <p class="text-sm text-gray-600 max-w-md mx-auto">
            Vista de host — tablero completo
          </p>
        </div>
      </div>
    </div>

    <!-- Modal con código de sesión -->
    <transition name="fade">
      <div v-if="showCodeModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          @click="cerrarModal"
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        ></div>

        <div class="bg-white rounded-3xl shadow-2xl p-6 md:p-8 w-full max-w-sm relative transform transition-all">
          <button
            @click="cerrarModal"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-700"
            aria-label="Cerrar"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="text-center">
            <div class="w-16 h-16 rounded-full bg-accent-yellow flex items-center justify-center mx-auto mb-4 shadow-lg">
              <span class="text-2xl">🎲</span>
            </div>

            <h3 class="text-xl font-bold text-gray-800 mb-2">¡Sesión creada!</h3>
            <p class="text-gray-600 mb-6">
              Comparte este código con los otros jugadores para que se unan a la partida.
            </p>

            <div class="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6">
              <span class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                Código de sesión
              </span>
              <div class="flex items-center gap-3">
                <span class="font-mono text-xl font-bold text-primary bg-white px-3 py-2 rounded-lg border border-gray-200 flex-1">
                  {{ createdCode }}
                </span>
              </div>
            </div>

            <button
              @click="irAlTablero"
              class="w-full py-4 rounded-xl font-bold text-white bg-primary hover:bg-secondary transition-all shadow-lg active:scale-95 mb-3"
            >
              Ir al tablero
            </button>
            <button
              @click="copiarCodigo"
              class="w-full py-4 rounded-xl font-bold text-accent-pink bg-accent-pink/10 border border-accent-pink/30 hover:bg-accent-pink/20 transition-all"
            >
              Compartir código (próximamente)
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Alert confirmación cerrar sesión -->
    <transition name="fade">
      <div v-if="confirmClose" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          @click="confirmClose = false"
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        ></div>

        <div class="bg-white rounded-3xl shadow-2xl p-6 md:p-8 w-full max-w-sm relative transform transition-all">
          <div class="text-center">
            <div class="w-12 h-12 rounded-full bg-accent-pink/10 flex items-center justify-center mx-auto mb-4">
              <span class="text-2xl">⚠️</span>
            </div>

            <h3 class="text-xl font-bold text-gray-800 mb-2">¿Cerrar la sesión?</h3>
            <p class="text-gray-600 mb-6">
              Al cerrar la sesión se guardarán los resultados y los jugadores serán desconectados.
              Esta acción no se puede deshacer.
            </p>

            <div class="flex gap-3">
              <button
                @click="confirmClose = false"
                class="flex-1 py-3 rounded-xl font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 transition-all"
              >
                Cancelar
              </button>
              <button
                @click="cerrarSesion"
                :disabled="loading"
                class="flex-1 py-3 rounded-xl font-bold text-white bg-accent-pink hover:bg-accent-pink/90 transition-all shadow-lg"
              >
                {{ loading ? 'Cerrando...' : 'Cerrar sesión' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal Ruleta -->
    <transition name="fade">
      <div v-if="showRuletaModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          @click="showRuletaModal = false"
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        ></div>

        <div class="bg-white rounded-3xl shadow-2xl p-6 w-full max-w-md relative transform transition-all">
          <button
            @click="showRuletaModal = false"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-700"
            aria-label="Cerrar"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="text-center">
            <h3 class="text-xl font-bold text-gray-800 mb-4">Ruleta</h3>

            <div class="w-48 h-48 rounded-full border-4 border-primary flex items-center justify-center mx-auto mb-6 relative overflow-hidden">
              <div class="absolute inset-0 border-4 border-transparent border-t-accent-pink rounded-full animate-spin"></div>
              <div class="text-3xl font-bold text-primary">🎰</div>
            </div>

            <button
              @click="showRuletaModal = false"
              class="w-full py-3 rounded-xl font-bold text-white bg-accent-pink hover:bg-accent-pink/90 transition-all shadow-lg"
            >
              Listo
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal Perfil (acordeón) -->
    <transition name="fade">
      <div v-if="showPerfilModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          @click="showPerfilModal = false"
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        ></div>

        <div class="bg-white rounded-3xl shadow-2xl p-6 w-full max-w-md relative transform transition-all max-h-[80vh] flex flex-col">
          <button
            @click="showPerfilModal = false"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-700"
            aria-label="Cerrar"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="flex-1 overflow-y-auto">
            <h3 class="text-xl font-bold text-gray-800 mb-4 text-center">Perfil del jugador</h3>

            <!-- Acordeón: Profesión -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 mb-3 overflow-hidden">
              <div class="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-100 transition-colors" @click="toggleAcordeon('profesion')">
                <span class="text-sm font-bold text-gray-700">Profesión</span>
                <span class="text-xs text-primary">{{ acordeonAbierto.profesion ? '▲' : '▼' }}</span>
              </div>
              <div v-if="acordeonAbierto.profesion" class="p-3 border-t border-gray-200">
                <p class="text-xs text-gray-600 mb-1">Empleo: <span class="font-medium">Empleado</span></p>
                <p class="text-xs text-gray-600">Sueldo: $50.000</p>
              </div>
            </div>

            <!-- Acordeón: Inversiones -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 mb-3 overflow-hidden">
              <div class="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-100 transition-colors" @click="toggleAcordeon('inversiones')">
                <span class="text-sm font-bold text-gray-700">Inversiones</span>
                <span class="text-xs text-primary">{{ acordeonAbierto.inversiones ? '▲' : '▼' }}</span>
              </div>
              <div v-if="acordeonAbierto.inversiones" class="p-3 border-t border-gray-200">
                <p class="text-xs text-gray-600 mb-1">Número: <span class="font-medium">7</span></p>
                <p class="text-xs text-gray-600">Monto: $100.000 · Escalón: 1</p>
              </div>
            </div>

            <!-- Acordeón: Casas -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 mb-3 overflow-hidden">
              <div class="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-100 transition-colors" @click="toggleAcordeon('casas')">
                <span class="text-sm font-bold text-gray-700">Casas</span>
                <span class="text-xs text-primary">{{ acordeonAbierto.casas ? '▲' : '▼' }}</span>
              </div>
              <div v-if="acordeonAbierto.casas" class="p-3 border-t border-gray-200">
                <p class="text-xs text-gray-600">Sin casas adquiridas</p>
              </div>
            </div>

            <!-- Acordeón: Familia -->
            <div class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
              <div class="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-100 transition-colors" @click="toggleAcordeon('familia')">
                <span class="text-sm font-bold text-gray-700">Familia</span>
                <span class="text-xs text-primary">{{ acordeonAbierto.familia ? '▲' : '▼' }}</span>
              </div>
              <div v-if="acordeonAbierto.familia" class="p-3 border-t border-gray-200">
                <p class="text-xs text-gray-600">Sin miembros de familia</p>
              </div>
            </div>
          </div>

          <button
            @click="showPerfilModal = false"
            class="w-full py-3 rounded-xl font-bold text-white bg-primary hover:bg-secondary transition-all shadow-lg mt-4"
          >
            Cerrar
          </button>
        </div>
      </div>
    </transition>

    <!-- Modal Tablero General -->
    <transition name="fade">
      <div v-if="verTableroGeneral" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          @click="verTableroGeneral = false"
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        ></div>

        <div class="bg-white rounded-3xl shadow-2xl p-6 w-full max-w-md relative transform transition-all max-h-[80vh] flex flex-col">
          <button
            @click="verTableroGeneral = false"
            class="absolute top-4 right-4 text-gray-400 hover:text-gray-700"
            aria-label="Cerrar"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="flex-1 overflow-y-auto">
            <h3 class="text-xl font-bold text-gray-800 mb-4 text-center">Tablero General</h3>

            <!-- Información de la sesión -->
            <div class="bg-secondary/5 rounded-xl p-4 border border-secondary/20 mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-secondary uppercase tracking-wider">Sesión</span>
                <span class="font-mono font-bold text-secondary">{{ boardSessionCode }}</span>
              </div>
              <p class="text-xs text-secondary-dark">
                {{ players.length }} jugador{{ players.length !== 1 ? 'es' : '' }} conectado{{ players.length !== 1 ? 's' : '' }}
              </p>
            </div>

            <!-- Lista de participantes con estado -->
            <div class="space-y-2">
              <div v-for="(player, idx) in players" :key="player.name" class="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-white">
                <div class="flex items-center gap-3">
                  <div
                    :class="['w-8 h-8 rounded-full flex items-center justify-center text-primary font-bold text-sm', player.is_creator ? 'bg-accent-pink' : 'bg-secondary']"
                  >
                    {{ player.name.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <span class="text-sm font-medium text-gray-800">{{ player.name }}</span>
                    <p v-if="player.is_creator" class="text-[10px] text-accent-pink font-bold uppercase">Creador</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-medium text-gray-500">Turno {{ idx + 1 }}</span>
                  <div class="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
              </div>
              <div v-if="players.length === 0" class="flex items-center justify-center h-20 text-xs text-gray-400">
                Sin participantes aún
              </div>
            </div>

            <!-- Leyenda de estados -->
            <div class="mt-4 bg-gray-50 rounded-xl p-3 border border-gray-200">
              <p class="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">Leyenda</p>
              <div class="flex gap-4 text-xs text-gray-600">
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                  Espera
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-green-500"></span>
                  Turno
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                  Jubilado
                </span>
              </div>
            </div>
          </div>

          <button
            @click="verTableroGeneral = false"
            class="w-full py-3 rounded-xl font-bold text-white bg-primary hover:bg-secondary transition-all shadow-lg mt-4"
          >
            Cerrar
          </button>
        </div>
      </div>
    </transition>

  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
