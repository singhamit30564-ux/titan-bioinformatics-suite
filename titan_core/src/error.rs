//! Shared error type for the titan_core crate.

use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoreError {
    /// Caller passed invalid input (bad path, empty payload, k out of range...).
    Input(String),
    /// A record/line could not be parsed; the message never contains sequence data.
    Parse(String),
    /// Operation was cancelled through a CancelToken.
    Cancelled,
    /// I/O failure (mmap, read).
    Io(String),
}

impl fmt::Display for CoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CoreError::Input(msg) => write!(f, "input error: {msg}"),
            CoreError::Parse(msg) => write!(f, "parse error: {msg}"),
            CoreError::Cancelled => write!(f, "operation cancelled"),
            CoreError::Io(msg) => write!(f, "io error: {msg}"),
        }
    }
}

impl std::error::Error for CoreError {}

impl From<std::io::Error> for CoreError {
    fn from(value: std::io::Error) -> Self {
        CoreError::Io(value.to_string())
    }
}

pub type Result<T> = std::result::Result<T, CoreError>;
