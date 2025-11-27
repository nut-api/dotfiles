return {
  {
    "nvim-telescope/telescope.nvim",
    keys = {
      -- add a keymap to browse plugin files
      -- stylua: ignore
      {
        "<leader>fh",
        function() require("telescope.builtin").find_files({ hidden = true }) end,
        desc = "Find Files (Hidden)",
      },
    },
    -- change some options
    opts = {
      defaults = {
        layout_strategy = "horizontal",
        layout_config = { prompt_position = "top" },
        sorting_strategy = "ascending",
        -- winblend = 0,
      },
    },
  },
}
