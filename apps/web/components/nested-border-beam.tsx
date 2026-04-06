import { BorderBeam } from "@workspace/ui/components/border-beam"

export function NestedBorderBeam() {
  return (
    <div className="flex w-full items-center justify-center bg-black py-20">
      <div className="relative inline-flex items-center justify-center rounded-[32px] border border-white/10 p-4 sm:p-6">
        <BorderBeam
          size={350}
          duration={8}
          delay={4}
          colorFrom="#ffffff"
          colorTo="#ffffff"
          borderWidth={1.5}
        />

        <div className="relative inline-flex items-center justify-center rounded-[24px] border border-white/10 p-4 sm:p-6">
          <BorderBeam
            size={250}
            duration={8}
            delay={2}
            colorFrom="#ffffff"
            colorTo="#ffffff"
            borderWidth={1.5}
          />

          <div className="relative inline-flex h-32 w-32 items-center justify-center rounded-2xl border border-white/10 sm:h-48 sm:w-48">
            <BorderBeam
              size={150}
              duration={8}
              delay={0}
              colorFrom="#ffffff"
              colorTo="#ffffff"
              borderWidth={1.5}
            />

            {/* You can place your central content here */}
          </div>
        </div>
      </div>
    </div>
  )
}
