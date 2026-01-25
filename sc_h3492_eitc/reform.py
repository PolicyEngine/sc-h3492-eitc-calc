"""South Carolina H.3492 Partially Refundable EITC reform definition."""

from policyengine_us.reforms.states.sc.h3492.sc_h3492_eitc_refundable import (
    sc_h3492_eitc_refundable,
)

# Use the pre-built reform from policyengine-us
# This reform makes 25% of the excess state EITC refundable
# The reform modifies SC tax variables to:
# - Split SC EITC into non-refundable and refundable portions
# - Refund 25% of the EITC amount exceeding tax liability
sc_h3492_reform = sc_h3492_eitc_refundable
