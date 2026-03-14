package com.automotive.sensor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope

import dagger.hilt.android.lifecycle.HiltViewModel

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

import javax.inject.Inject

// GOOD: sealed interface models UI state exhaustively
sealed interface SensorUiState {
    object Loading : SensorUiState
    data class Success(val tempDegC: Float) : SensorUiState
    data class Error(val message: String)   : SensorUiState
}

/**
 * ViewModel for the sensor dashboard screen.
 *
 * Exposes [uiState] as an immutable [StateFlow]; never exposes mutable state directly.
 * All data work delegated to [SensorRepository] — no business logic here.
 */
@HiltViewModel                                      // GOOD: Hilt-managed ViewModel
class GoodSensorViewModel @Inject constructor(
    private val repo: SensorRepository              // GOOD: depends on interface, not impl
) : ViewModel() {

    // GOOD: private mutable, public immutable — callers cannot push state
    private val _uiState = MutableStateFlow<SensorUiState>(SensorUiState.Loading)
    val uiState: StateFlow<SensorUiState> = _uiState.asStateFlow()

    init {
        load(channel = 3)
    }

    /**
     * Loads temperature for [channel] and updates [uiState].
     * Cancels any previous in-flight load automatically (viewModelScope is cancelled on clear).
     */
    fun load(channel: Int) {
        require(channel in 0..7) { "channel must be 0–7, got $channel" } // GOOD: precondition
        viewModelScope.launch {                     // GOOD: structured scope, not GlobalScope
            _uiState.value = SensorUiState.Loading
            repo.readDegC(channel)
                .onSuccess { _uiState.value = SensorUiState.Success(it) }
                .onFailure { _uiState.value = SensorUiState.Error(it.message ?: "Unknown error") }
        }
    }

    fun refresh() = load(channel = 3)
}
