return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        sources = {
          grep = {
            hidden = true,
            exclude = { "**/.git/*" },
          },
        },
      },
    },
  },
}
