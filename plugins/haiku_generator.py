"""Haiku Generator — Example Titan Plugin.

Generates random biology-themed haikus (5-7-5 syllable pattern).
"""
import random

PLUGIN_NAME = "Haiku Generator"
PLUGIN_DESCRIPTION = "Generate random biology-themed haikus."
PLUGIN_AUTHOR = "Titan Community"

_TEMPLATES = [
    ("DNA uncoils", "Adenine meets Thymine now", "Life's code revealed here"),
    ("Ribosomes spin", "mRNA threads through the groove", "Proteins take their shape"),
    ("Mitochondria", "Powerhouse of every cell", "ATP flows free"),
    ("Single cell divides", "Chromosomes line up and split", "Two from one alive"),
    ("PCR cycles", "Denature, anneal, extend", "Millions from a trace"),
    ("CRISPR cuts the strand", "Guide RNA finds the target", "Genes rewrite fate"),
    ("Phylogenetic tree", "Branches split from common root", "Life's diversity"),
    ("Neurons fire fast", "Synapses spark thought and dream", "Consciousness ignites"),
    ("Chloroplast glows green", "Light reactions capture sun", "Sugar from the sky"),
    ("Petri dish in hand", "Bacteria grow in neat rows", "Micro world alive"),
]


def run() -> None:
    """Entry point for the plugin (not Streamlit-dependent)."""
    return random.choice(_TEMPLATES)