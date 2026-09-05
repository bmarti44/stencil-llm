
## Measured throughput decision (before competence/profiles)

{
  "trials_tps": [
    16.018709682551172,
    17.267650974020473,
    17.374734875241437
  ],
  "conservative_tps": 16.018709682551172,
  "prefill_tokens": 2048,
  "prefill_seconds": 0.7469094039406627,
  "full": {
    "scaled": false,
    "episodes": 64,
    "alpha": [
      0.5,
      1,
      2,
      4
    ],
    "layers": [
      "all",
      "upper_half"
    ],
    "competence_requests": 192,
    "profile_forwards": 256,
    "grid_requests": 256,
    "final_requests": 1984,
    "capped_decode_tokens": 622592,
    "seconds": 51962.68628946622,
    "fits": false
  },
  "scaled": {
    "scaled": true,
    "episodes": 32,
    "alpha": [
      1,
      4
    ],
    "layers": [
      "all"
    ],
    "competence_requests": 192,
    "profile_forwards": 256,
    "grid_requests": 64,
    "final_requests": 992,
    "capped_decode_tokens": 319488,
    "seconds": 27204.918359798612,
    "fits": false
  },
  "selected": {
    "scaled": true,
    "episodes": 32,
    "alpha": [
      1,
      4
    ],
    "layers": [
      "all"
    ],
    "competence_requests": 192,
    "profile_forwards": 256,
    "grid_requests": 64,
    "final_requests": 992,
    "capped_decode_tokens": 319488,
    "seconds": 27204.918359798612,
    "fits": false
  },
  "kernel": {
    "candidate": "grouped_mm",
    "available": true,
    "adopted": true,
    "relative_error": 0.0,
    "experts_implementation": {
      "": "grouped_mm"
    },
    "nonzero_dispatch_verified": true,
    "exact_off_next_logits": true
  }
}
